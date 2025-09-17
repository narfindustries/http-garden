#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"

if [ "$#" -eq 0 ]; then
    set -- 'help'
fi

build_soil() {
    docker pull debian:trixie-slim
    docker build "./images/http-garden-soil" -t http-garden-soil
}

case "$1" in
    repl)
        which rlwrap &>/dev/null && rlwrap python3 ./tools/repl.py || python3 ./tools/repl.py
    ;;

    build_seq)
        build_soil
        for container in $([ "$#" -eq 1 ] && python3 -c 'import yaml; print(*yaml.safe_load(open("./docker-compose.yml"))["services"].keys())' || echo "${@:2}"); do
            docker compose build "$container"
        done
    ;;

    build)
        build_soil
        docker compose build "${@:2}"
    ;;

    start)
        build_soil
        docker compose up "${@:2}"
    ;;

    stop)
        docker compose down
    ;;

    probe_quirks)
        if python3 ./tools/probe_quirks.py > out.yml; then
            mv out.yml quirks.yml
        else
            rm out.yml
        fi
    ;;

    update)
        if python3 ./tools/update.py > out.yml; then
            mv out.yml docker-compose.yml
        else
            rm out.yml
        fi
    ;;
    
    *)
        echo "Usage: $0 [repl | start *[container] | build *[container] | stop | update]"
    ;;
esac
