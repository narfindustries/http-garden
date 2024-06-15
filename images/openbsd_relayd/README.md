# OpenBSD relayd

The OpenBSD relayd can't be installed on Linux.
Instead of providing a Docker image here, I'll provide instructions for setting up httpd on a VPS.

1. Get an OpenBSD VPS with a public IPv4 and SSH to it. (Vultr's cheapest option is $3.50/month at the time of writing.)
2. Upgrade to the latest snapshot:
```sh
$ sysupgrade -s
```
3. Wait for it to come back up. Give it like 30 minutes.
4. Copy the following into `/etc/relayd.conf`. Fill in the blanks with your echo server details:
```
http protocol "the_protocol" {
    pass
}

relay "the_relay" {
    listen on 0.0.0.0 port 80
    protocol "the_protocol"
    forward to <FILL ME IN> port <FILL ME IN>
}
```
5. Start relayd:
```sh
$ relayd
```
