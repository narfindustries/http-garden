FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends bmake byacc libbsd-dev libtls-dev libssl-dev groff php-fpm libevent-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
ARG OPENBSD_SRC_REPO
ARG OPENBSD_SRC_VERSION
RUN cd obhttpd-linux \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && export OPENBSD_SRC_REPO OPENBSD_SRC_VERSION \
 && ./patch.sh \
 && sed -i "s/\(LDADD+=.*\)/\1 $LDFLAGS/" Makefile \
 && bmake \
 && rm -rf src

RUN mkdir -p /var/www/htdocs \
 && useradd --home-dir /var/www www \
 && sed -i 's/listen = \/.*/listen = 127.0.0.1:9000/' /etc/php/8.4/fpm/pool.d/www.conf

COPY httpd.conf /etc/httpd.conf
COPY index.php /var/www/htdocs/index.php

WORKDIR /app/obhttpd-linux
CMD php-fpm8.4 \
 && export ASAN_SYMBOLIZER_PATH=/usr/bin/llvm-symbolizer-19 \
 && exec ./httpd -vd
