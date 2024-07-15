FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends php-fpm git libpcre2-dev zlib1g-dev libssl-dev libxml2-dev libxslt-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

RUN sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/8.2/fpm/pool.d/www.conf

# I used to use UBSan here, but it actually finds too much stuff and gets in the way...

ARG APP_VERSION
RUN cd /app/nginx && git pull && git checkout "$APP_VERSION" && ./auto/configure --with-cc="$(which afl-cc)" --with-cc-opt="-fsanitize=address" --with-ld-opt='-fsanitize=address' && make -j"$(nproc)" && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/nginx/conf/nginx.conf

COPY ./index.php /usr/local/nginx/html/index.php

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/nginx/conf/nginx.conf

RUN groupadd nobody

CMD php-fpm8.2 \
 && export AFL_MAP_SIZE="$(afl-showmap -o /dev/null -t 2147483647 -- /usr/local/nginx/sbin/nginx 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}')" \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- /usr/local/nginx/sbin/nginx
