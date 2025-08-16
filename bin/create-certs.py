#!/bin/env python3

import os
import subprocess
import getpass
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

npm_token = os.getenv("NGINX_PROXY_MANAGER_TOKEN")
npm_base_url = os.getenv("NGINX_PROXY_MANAGER_BASE_URL", "http://localhost:81/api")

npm_proxy_hosts = None

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def npm_get_token():
    """
    Get the Nginx-Proxy Manager (npm) token from the user or cache it if already obtained.
    If the token is already cached, it will return the cached value.
    If not, it will prompt the user for their npm credentials (email and password),
    and request a token from the npm API.
    The token is cached for future use.
    """
    global npm_token
    if (npm_token):
        logger.debug("Returning cached npm_token.")
        return npm_token
    print("Credentials for Nginx-Proxy Manager (npm):")
    identity = input("e-mail: ").strip()
    password = getpass.getpass("password: ").strip()

    logger.debug(f"Requesting npm token for identity: {identity}")
    response = requests.post(
        f"{npm_base_url}/tokens",
        json={
            "identity": identity, 
            "secret": password,
        },
        verify=False,
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")

    if response.status_code == 200:
        npm_token = response.json().get("token")
        logger.debug(f"npm_token obtained: {npm_token}")

def generate_cert(dns_name, ca_key_pass=None):
    out_dir = f"temp/certs/{dns_name}"
    os.makedirs(out_dir, exist_ok=True)

    key_path = f"{out_dir}/cert-key.pem"
    csr_path = f"{out_dir}/cert.csr"
    extfile_path = f"{out_dir}/extfile.cnf"
    cert_path = f"{out_dir}/cert.pem"
    fullchain_path = f"{out_dir}/fullchain.pem"
    ca_cert = "temp/ca/ca.pem"
    ca_key = "temp/ca/ca-key.pem"

    subprocess.run(["openssl", "genrsa", "-out", key_path, "4096"], check=True)
    subprocess.run([
        "openssl", "req", "-new", "-sha256", "-subj", "/CN=homelab", "-key", key_path, "-out", csr_path
    ], check=True)

    with open(extfile_path, "w") as f:
        f.write(f"subjectAltName=DNS:{dns_name}\n")

    x509_cmd = [
        "openssl", "x509", "-req", "-sha256", "-days", "365", "-in", csr_path,
        "-CA", ca_cert, "-CAkey", ca_key, "-out", cert_path,
        "-extfile", extfile_path, "-CAcreateserial"
    ]
    if ca_key_pass:
        x509_cmd.extend(["-passin", f"pass:{ca_key_pass}"])
    subprocess.run(x509_cmd, check=True)

    with open(fullchain_path, "w") as f:
        with open(cert_path, "r") as cert_file:
            f.write(cert_file.read())
        with open(ca_cert, "r") as ca_file:
            f.write(ca_file.read())
    logger.debug(f"Certificate and key generated for {dns_name} in {out_dir}")

def npm_create_cert(hostname):
    response = requests.post(
        f"{npm_base_url}/nginx/certificates",
        json={
            "nice_name": hostname,
            "provider": "other"
        },
        headers={
            "Authorization": f"Bearer {npm_get_token()}",
        },
        verify=False,
    )

    if response.status_code == 201:
        logger.debug(f"Certificate for {hostname} created successfully.")
    else:
        logger.error(f"Failed to create certificate for {hostname}: {response.status_code} - {response.text}")
        raise Exception(f"Failed to create certificate: {response.status_code} - {response.text}")
    return response.json().get("id")

def npm_upload_cert(cert_id, hostname):
    cert_path = f"temp/certs/{hostname}/fullchain.pem"
    key_path = f"temp/certs/{hostname}/cert-key.pem"
    url = f"{npm_base_url}/nginx/certificates/{cert_id}/upload"

    with open(cert_path, "rb") as cert_file, open(key_path, "rb") as key_file:
        response = requests.post(
            url,
            files={
                "certificate": ("cert.pem", cert_file, "application/x-x509-ca-cert"),
                "certificate_key": ("cert-key.pem", key_file, "application/x-x509-ca-cert"),
            },
            headers={
                "Authorization": f"Bearer {npm_get_token()}",
            },
            verify=False,
        )

    if response.status_code == 200:
        logger.debug(f"Certificate for {hostname} uploaded successfully.")
    else:
        logger.error(f"Failed to upload certificate for {hostname}: {response.status_code} - {response.text}")

def npm_list_proxy_hosts():
    global npm_proxy_hosts
    if npm_proxy_hosts is not None and len(npm_proxy_hosts) > 0:
        return npm_proxy_hosts

    response = requests.get(
        f"{npm_base_url}/nginx/proxy-hosts",
        headers={
            "Authorization": f"Bearer {npm_get_token()}",
        },
        verify=False,
    )
    if response.status_code == 200:
        npm_proxy_hosts = response.json()
        logger.debug(f"Retrieved {len(npm_proxy_hosts)} proxy hosts from npm.")
    else:
        logger.error(f"Failed to retrieve proxy hosts: {response.status_code} - {response.text}")
        raise Exception(f"Failed to retrieve proxy hosts: {response.status_code} - {response.text}")

    return npm_proxy_hosts

def npm_get_proxy_host(hostname):
    """
    Get the proxy host ID for a given hostname.
    If the hostname is not found, it returns None.
    """
    npm_hosts = npm_list_proxy_hosts()
    for host in npm_hosts:
        if host.get("domain_names") and hostname in host["domain_names"]:
            return host["id"]
    return None

def npm_set_proxy_host_certificate(hostname, cert_id):
    """
    Set the certificate for a proxy host.
    """
    host_id = npm_get_proxy_host(hostname)
    if not host_id:
        logger.error(f"Proxy host for {hostname} not found.")
        return

    response = requests.put(
        f"{npm_base_url}/nginx/proxy-hosts/{host_id}",
        json={
            "certificate_id": cert_id,
            'ssl_forced': True,
            'http2_support': True,
            'access_list_id': '1'
        },
        headers={
            "Authorization": f"Bearer {npm_get_token()}",
        },
        verify=False,
    )

    if response.status_code == 200:
        logger.debug(f"Certificate set for proxy host {hostname} successfully.")
    else:
        logger.error(f"Failed to set certificate for proxy host {hostname}: {response.status_code} - {response.text}")

def npm_delete_unused_certs():
    """
    Delete unused certificates from Nginx-Proxy Manager.
    """
    response = requests.get(
        f"{npm_base_url}/nginx/certificates?expand=proxy_hosts",
        headers={
            "Authorization": f"Bearer {npm_get_token()}",
        },
        verify=False,
    )

    if response.status_code != 200:
        logger.error(f"Failed to retrieve certificates: {response.status_code} - {response.text}")
        return

    certs = response.json()
    for cert in certs:
        proxy_hosts = cert.get("proxy_hosts", [])
        logger.debug(f"Checking certificate ID {cert['id']} with domain names: {proxy_hosts}")
        if len(proxy_hosts) == 0:
            logger.debug(f"Certificate ID {cert['id']} is unused, deleting it.")
            cert_id = cert["id"]
            delete_response = requests.delete(
                f"{npm_base_url}/nginx/certificates/{cert_id}",
                headers={
                    "Authorization": f"Bearer {npm_get_token()}",
                },
                verify=False,
            )
            if delete_response.status_code == 204:
                logger.debug(f"Deleted unused certificate ID {cert_id}.")
            else:
                logger.error(f"Failed to delete certificate ID {cert_id}: {delete_response.status_code} - {delete_response.text}")

if __name__ == "__main__":
    ca_key_pass = getpass.getpass("Enter CA key passphrase (leave empty if not needed): ").strip() or None
    for host in npm_list_proxy_hosts():
        domain_names = host.get("domain_names", [])
        for domain in domain_names:
            if domain:
                hostname = domain.strip()
                logger.debug(f"Processing hostname: {hostname}")

                # generate a certificate for the hostname
                generate_cert(hostname, ca_key_pass=ca_key_pass)

                # create npm certificate
                cert_id = npm_create_cert(hostname)

                # upload the certificate to npm
                npm_upload_cert(cert_id, hostname)

                # set the certificate for the proxy host
                npm_set_proxy_host_certificate(hostname, cert_id)
            else:
                logger.warning("Empty domain name found, skipping.")

    # Clean up unused certificates
    npm_delete_unused_certs()