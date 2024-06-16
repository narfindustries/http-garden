FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-docutils python3-sphinx autoconf automake ca-certificates libedit-dev libtool linux-headers-amd64 libpcre2-dev libunwind-dev pkg-config && git clone "https://github.com/varnishcache/varnish-cache"

ARG APP_VERSION
RUN cd varnish-cache && git pull && git checkout "$APP_VERSION" && ./autogen.sh && ./configure --with-unwind CC='afl-cc' CFLAGS='-fsanitize=address,undefined' LDFLAGS='-fsanitize=address,undefined' && make -j$(nproc) && make install

COPY ./config.vcl /app/config.vcl

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/config.vcl

# Couldn't get afl-showmap to work. Leaving this as untraced, but still todo
CMD export AFL_MAP_SIZE="$(AFL_DEBUG=1 afl-showmap -o /dev/null -t 2147483647 -- /app/varnish-cache/bin/varnishd/varnishd -F -f /app/config.vcl -a http=:80,HTTP -p feature=+http2 -s malloc,2G -p default_keep=300 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}')" \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- /app/varnish-cache/bin/varnishd/varnishd -F -f /app/config.vcl -a http=:80,HTTP -p feature=+http2 -s malloc,2G -p default_keep=300
