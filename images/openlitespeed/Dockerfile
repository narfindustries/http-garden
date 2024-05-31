FROM debian:bullseye-slim

WORKDIR /app

RUN apt -y update && apt -y install wget curl php-fpm ncat

RUN mkdir /run/php

ARG APP_VERSION
RUN wget "https://github.com/litespeedtech/openlitespeed/releases/download/v${APP_VERSION}/openlitespeed-${APP_VERSION}-x86_64-linux.tgz" && tar xf openlitespeed*.tgz

RUN cd /app/openlitespeed && ./install.sh

RUN rm -rf /usr/local/lsws/Example && mkdir /usr/local/lsws/the_vhost
COPY echo.php /usr/local/lsws/the_vhost/echo.php

RUN cp /usr/local/lsws/conf/mime.properties /tmp && rm -rf /usr/local/lsws/conf && mkdir /usr/local/lsws/conf && mv /tmp/mime.properties /usr/local/lsws/conf/mime.properties

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/lsws/conf/httpd_config.conf

ARG VHOST_CONFIG_FILE
COPY $VHOST_CONFIG_FILE /usr/local/lsws/conf/the_vhost.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/lsws/conf/httpd_config.conf

CMD php-fpm7.4 && chown nobody:nogroup /run/php/php7.4-fpm.sock && /usr/local/lsws/bin/litespeed && sleep infinity
