#!/bin/bash

set -euo pipefail

rm -f /usr/local/apache2/logs/httpd.pid

php-fpm8.4

/usr/local/apache2/bin/httpd -X
