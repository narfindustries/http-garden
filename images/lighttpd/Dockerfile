FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends autoconf automake libtool m4 pkg-config libpcre2-dev nettle-dev bzip2 libbrotli-dev libdeflate-dev libunwind-dev zlib1g-dev libzstd-dev php-fpm

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/lighttpd1.4 \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./autogen.sh \
 && ./configure \
 && make "-j$(nproc)" install

RUN mkdir /app/www \
 && sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/8.2/fpm/pool.d/www.conf \
 && useradd http

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/lighttpd.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/lighttpd.conf

COPY ./index.php /app/www

CMD export AFL_PRELOAD="$(echo /usr/local/lib/*.so | sed 's/ /:/g')" \
           AFL_MAP_SIZE="$(afl-showmap -o /dev/null -t 2147483647 -- lighttpd -f /app/lighttpd.conf -D 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}')" \
 && php-fpm8.2 \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- lighttpd -f /app/lighttpd.conf -D
