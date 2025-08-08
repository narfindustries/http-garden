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
 && sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/8.4/fpm/pool.d/www.conf \
 && useradd http

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/lighttpd.conf

ARG BACKEND_HOST
ARG BACKEND_PORT
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /app/lighttpd.conf

COPY ./index.php /app/www

CMD php-fpm8.4 \
 && exec lighttpd -f /app/lighttpd.conf -D
