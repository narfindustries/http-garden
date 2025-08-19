#!/bin/bash

set -euo pipefail

php-fpm8.4

haproxy -f /app/haproxy.conf
