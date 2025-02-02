FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends php-fpm git libpcre2-dev zlib1g-dev libssl-dev libxml2-dev libxslt-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# Disabling sanitizers and AFL for now because it's too annoying to debug.

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/nginx \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && ./auto/configure \
 && make "-j$(nproc)" \
 && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/nginx/conf/nginx.conf
COPY ./index.php /usr/local/nginx/html/index.php

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/nginx/conf/nginx.conf

RUN groupadd nobody && sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/8.4/fpm/pool.d/www.conf

CMD php-fpm8.4 \
 && exec /usr/local/nginx/sbin/nginx
