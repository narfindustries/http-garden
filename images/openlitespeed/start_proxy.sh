#!/bin/bash

set -euo pipefail

python3 /tools/echo_server.py --host-url "http://127.0.0.1:$((0xdafe))" --pcap-url "http://0.0.0.0:$((0xda1e))" &

/usr/local/lsws/bin/litespeed

sleep infinity
