FROM debian:bullseye-slim

WORKDIR /app

RUN apt -y update && apt -y install --no-install-recommends wget curl php-fpm ncat ca-certificates

RUN mkdir /run/php

ARG APP_VERSION
ARG APP_BRANCH
RUN wget "https://github.com/litespeedtech/openlitespeed/releases/download/${APP_BRANCH}/openlitespeed-${APP_VERSION}-$(uname -m)-linux.tgz" -O openlitespeed.tgz && tar xf openlitespeed.tgz

RUN cd /app/openlitespeed && ./install.sh && rm -rf /usr/local/lsws/Example && mkdir /usr/local/lsws/the_vhost
COPY echo.php /usr/local/lsws/the_vhost/echo.php

RUN cp /usr/local/lsws/conf/mime.properties /tmp && rm -rf /usr/local/lsws/conf && mkdir /usr/local/lsws/conf && mv /tmp/mime.properties /usr/local/lsws/conf/mime.properties

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/lsws/conf/httpd_config.conf

ARG VHOST_CONFIG_FILE
COPY $VHOST_CONFIG_FILE /usr/local/lsws/conf/the_vhost.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/lsws/conf/httpd_config.conf && sed -i 's/^pm\.max_children = 5$/pm.max_children = 500/' /etc/php/7.4/fpm/pool.d/www.conf

CMD php-fpm7.4 && chown nobody:nogroup /run/php/php7.4-fpm.sock && /usr/local/lsws/bin/litespeed && sleep infinity
