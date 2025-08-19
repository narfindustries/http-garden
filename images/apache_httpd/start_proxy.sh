#!/bin/bash

set -euo pipefail

python3 /tools/echo_server.py --host-url "http://127.0.0.1:$((0xdafe))" --pcap-url "http://0.0.0.0:$((0xda1e))" &

rm -f /usr/local/apache2/logs/httpd.pid

/usr/local/apache2/bin/httpd -X
