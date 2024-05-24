FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install zlib1g-dev libpcre2-dev libssl-dev php-fpm && git clone "https://github.com/haproxy/haproxy"

ARG APP_VERSION
# We're not using UBSan or ASan here because HAProxy complains when you override CFLAGS.
RUN cd haproxy && git checkout $APP_VERSION && make -j$(nproc) CC='afl-cc' TARGET=linux-glibc USE_OPENSSL=1 USE_ZLIB=1 USE_PCRE2=1 && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/haproxy.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/haproxy.conf

RUN mkdir /var/www
COPY ./index.php /var/www

CMD php-fpm8.2 \
 && export AFL_MAP_SIZE="$(AFL_DEBUG=1 afl-showmap -o /dev/null -t 2147483647 -- haproxy -f /app/haproxy.conf 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}')" \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- haproxy -f /app/haproxy.conf
