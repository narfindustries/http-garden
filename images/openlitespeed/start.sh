#!/bin/bash

set -euo pipefail

php-fpm8.4

chown nobody:nogroup /run/php/php8.4-fpm.sock

/usr/local/lsws/bin/litespeed

sleep infinity
