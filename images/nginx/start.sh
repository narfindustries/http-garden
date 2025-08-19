#!/bin/bash

set -euo pipefail

php-fpm8.4

/usr/local/nginx/sbin/nginx
