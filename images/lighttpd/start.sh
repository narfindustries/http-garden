#!/bin/bash

set -euo pipefail

php-fpm8.4

lighttpd -f /app/lighttpd.conf -D
