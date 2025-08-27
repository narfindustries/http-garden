#!/bin/bash

set -euo pipefail

python3 /tools/echo_server.py 127.0.0.1 "$((0xdafe))" &

rm -f /usr/local/apache2/logs/httpd.pid

/usr/local/apache2/bin/httpd -X
