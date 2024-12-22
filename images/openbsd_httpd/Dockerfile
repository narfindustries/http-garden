FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends bmake byacc libbsd-dev libtls-dev libssl-dev groff php-fpm libevent-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG OPENBSD_SRC_REPO
ARG OPENBSD_SRC_VERSION
RUN cd obhttpd-linux \
 && git pull \
 && git checkout "$APP_VERSION" \
 && export OPENBSD_SRC_REPO OPENBSD_SRC_VERSION \
 && ./patch.sh \
 && export CFLAGS='-fsanitize=address,undefined' \
 && sed -i 's/\(LDADD+=.*\)/\1 -fsanitize=address,undefined/' Makefile \
 && bmake

RUN mkdir -p /var/www/htdocs && useradd --home-dir /var/www www && sed -i 's/listen = \/.*/listen = 127.0.0.1:9000/' /etc/php/8.2/fpm/pool.d/www.conf

COPY httpd.conf /etc/httpd.conf
COPY index.php /var/www/htdocs/index.php

CMD php-fpm8.2 && exec ./obhttpd-linux/httpd -vd
