FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends autoconf libtool libtool-bin libexpat1-dev libpcre2-dev libnghttp2-dev php-fpm \
 && sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/8.4/fpm/pool.d/www.conf

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APR_REPO
RUN cd httpd/srclib \
 && git clone --recurse-submodules "$APR_REPO"

ARG APR_VERSION
ARG APP_VERSION
RUN cd /app/httpd/srclib/apr \
 && git pull origin "$APR_BRANCH" \
 && git checkout "$APR_VERSION" \
 && cd /app/httpd \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./buildconf \
 && ./configure --enable-proxy-http2 \
 && make "-j$(nproc)" \
 && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/apache2/conf/httpd.conf

ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /usr/local/apache2/conf/httpd.conf \
 && mkdir -p /var/www

COPY ./index.php /var/www

ARG START_SCRIPT
COPY $START_SCRIPT ./start.sh
CMD ["./start.sh"]
