## Troubleshooting

### Port 53 already in use

Port 53 must be already in use by default.

To resolve this issue :

- Create the file `/etc/systemd/resolved.conf.d/adguardhome.conf` (create the folder if necessary)

- Add the following content in the file :

```txt
[Resolve]
DNS=127.0.0.1
DNSStubListener=no
```

- Make a backup of the current `/etc/resolv.conf` file

- Create a symbolic link for the compiled resolv.conf

```sh
sudo ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
```

- Reload and restart the systemd-resolved service


```sh
systemctl reload-or-restart systemd-resolved
```

> src: https://github.com/AdguardTeam/AdGuardHome/issues/4283#issuecomment-1037397445

### Misbehaving

Restart portainer or the current container trying to access the DNS