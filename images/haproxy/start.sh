#!/bin/bash

set -euo pipefail

python3 /tools/echo_server.py --host-url 'http://127.0.0.1:56062' --pcap-url 'http://0.0.0.0:55838' &

haproxy -f /app/haproxy.conf
