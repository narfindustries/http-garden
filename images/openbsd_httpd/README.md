# OpenBSD httpd

The OpenBSD httpd can't be installed on Linux [without heavy patching](https://github.com/FreakyPenguin/openbsd-httpd-linux).
Instead of providing a Docker image here, I'll provide instructions for setting up httpd on a VPS.

1. Get an OpenBSD VPS with a public IPv4 and SSH to it. (Vultr's cheapest option is $3.50/month at the time of writing.)
2. Upgrade to the latest snapshot:
```sh
$ sysupgrade -s
```
3. Wait for it to come back up. Give it like 30 minutes.
4. Install PHP:
```sh
$ pkg_add php
$ # If it asks about versions, it doesn't matter which you pick.
```
5. Copy the following into `/etc/httpd.conf`:
```
prefork 1

server "default" {
    listen on * port 80
    root "/htdocs"
    fastcgi {
        param SCRIPT_FILENAME "/htdocs/index.php"
        socket "/run/php-fpm.sock"
    }
}
```
6. Copy the following into `/var/www/htdocs/index.php`:
```php
<?php
    $encoded_headers = [];
    foreach (apache_request_headers() as $name => $value) {
        array_push($encoded_headers, [base64_encode($name), base64_encode($value)]);
    }

    $request = [
        'headers' => $encoded_headers,
        'body' => base64_encode(file_get_contents('php://input')),
        'method' => base64_encode($_SERVER['REQUEST_METHOD']),
        'uri' => base64_encode($_SERVER['REQUEST_URI']),
        'version' => base64_encode($_SERVER['SERVER_PROTOCOL'])
    ];

    echo json_encode($request);
?>
```
7. Start PHP-FPM:
```sh
$ php-fpm-8.2 # You may have to change the version here
```
8. Start httpd:
```sh
$ httpd
```
