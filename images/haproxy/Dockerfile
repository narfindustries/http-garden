FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends zlib1g-dev libpcre2-dev libssl-dev php-fpm

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

COPY fix_ub.patch ./haproxy

ARG APP_VERSION
RUN cd haproxy \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && git apply fix_ub.patch \
 && make "-j$(nproc)" CC="$CC" CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS" TARGET=linux-glibc USE_OPENSSL=1 USE_ZLIB=1 USE_PCRE2=1 \
 && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/haproxy.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/haproxy.conf \
 && mkdir /var/www
COPY ./index.php /var/www

CMD php-fpm8.4 \
 && exec haproxy -f /app/haproxy.conf
