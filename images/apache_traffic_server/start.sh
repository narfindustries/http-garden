#!/bin/bash

set -euo pipefail

python3 /tools/echo_server.py 127.0.0.1 "$((0xdafe))" &

/app/trafficserver/build-default/src/traffic_server/traffic_server --httpport 80
