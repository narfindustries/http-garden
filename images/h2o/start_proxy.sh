#!/bin/bash

set -euo pipefail

python3 /tools/echo_server.py 127.0.0.1 "$((0xdafe))" &

h2o -c /app/h2o.conf
