FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install mercurial libpcre2-dev zlib1g-dev libssl-dev libxml2-dev libxslt-dev && hg clone "http://hg.nginx.org/nginx/" && hg clone "http://hg.nginx.org/njs"

# I used to use UBSan here, but it actually finds too much stuff and gets in the way...

ARG APP_VERSION
RUN cd /app/nginx && hg update $APP_VERSION && ./auto/configure --with-cc="$(which afl-cc)" --with-cc-opt="-fsanitize=address" --with-ld-opt='-fsanitize=address' --add-dynamic-module=/app/njs/nginx && make -j$(nproc) && make install

COPY ./index.js /app

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/nginx/conf/nginx.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/nginx/conf/nginx.conf

RUN groupadd nobody

CMD export AFL_MAP_SIZE="$(AFL_DEBUG=1 afl-showmap -o /dev/null -t 2147483647 -- /usr/local/nginx/sbin/nginx 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}')" \
           AFL_PRELOAD="/usr/local/nginx/$(cat /usr/local/nginx/conf/nginx.conf | grep -oP 'load_module [^;]*' | awk '{print $2}')" \
           ASAN_OPTIONS=detect_odr_violation=0 \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- /usr/local/nginx/sbin/nginx
