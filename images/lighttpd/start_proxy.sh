#!/bin/bash

set -euo pipefail

python3 /tools/echo_server.py 127.0.0.1 "$((0xdafe))" &

lighttpd -f /app/lighttpd.conf -D
