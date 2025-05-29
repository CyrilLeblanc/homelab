Port 53 must be already in use by default.

```sh
sudo mkdir /etc/systemd/resolved.conf.d
cd /etc/systemd/resolved.conf.d
sudo nano adguardhome.conf
```

put this content in the file :

```txt
[Resolve]
DNS=127.0.0.1
DNSStubListener=no
```

```sh
sudo mv /etc/resolv.conf /etc/resolv.conf.backup
sudo ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
systemctl reload-or-restart systemd-resolved
```

> src: https://github.com/AdguardTeam/AdGuardHome/issues/4283#issuecomment-1037397445