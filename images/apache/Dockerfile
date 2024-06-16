FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install autoconf libtool libtool-bin libexpat1-dev libpcre2-dev libnghttp2-dev php-fpm && git clone "https://github.com/apache/httpd" && cd httpd/srclib && git clone "https://github.com/apache/apr"

ARG APP_VERSION
RUN cd /app/httpd && git pull && git checkout "$APP_VERSION" && ./buildconf && ./configure CC='afl-cc' CFLAGS='-fsanitize=undefined,address' LDFLAGS='-fsanitize=undefined,address' && make -j$(nproc) && make install

RUN sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/8.2/fpm/pool.d/www.conf

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/apache2/conf/httpd.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/apache2/conf/httpd.conf && mkdir -p /var/www

COPY ./index.php /var/www

RUN grep -oP 'mod_.*\.so' /usr/local/apache2/conf/httpd.conf | sed 's/^/\/usr\/local\/apache2\/modules\//g' | tr '\n' ':' | head -c -1 > afl_preload
RUN AFL_DEBUG=1 afl-showmap -o /dev/null -t 2147483647 -- /usr/local/apache2/bin/httpd -X 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}' > afl_map_size

CMD rm -f /usr/local/apache2/logs/httpd.pid \
 && php-fpm8.2 \
 && export AFL_PRELOAD="$(cat afl_preload)" \
 && export AFL_MAP_SIZE="$(cat afl_map_size)" \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- /usr/local/apache2/bin/httpd -X
