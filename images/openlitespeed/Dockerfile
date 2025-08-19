FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends git libudns-dev php-fpm

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd openlitespeed \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && sed -i -e 's/CUR_PATH/CURDIR/' ./build.sh \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && ./build.sh -p OFF -o OFF -l OFF -d \
 && ./install.sh

RUN rm -rf /usr/local/lsws/Example && mkdir /usr/local/lsws/the_vhost
COPY echo.php /usr/local/lsws/the_vhost/echo.php

RUN cp /usr/local/lsws/conf/mime.properties /tmp && rm -rf /usr/local/lsws/conf && mkdir /usr/local/lsws/conf && mv /tmp/mime.properties /usr/local/lsws/conf/mime.properties

ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/lsws/conf/httpd_config.conf

ARG VHOST_CONFIG_FILE
COPY $VHOST_CONFIG_FILE /usr/local/lsws/conf/the_vhost.conf

ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /usr/local/lsws/conf/httpd_config.conf && sed -i 's/^pm\.max_children = 5$/pm.max_children = 500/' /etc/php/8.4/fpm/pool.d/www.conf

ARG START_SCRIPT
COPY $START_SCRIPT ./start.sh
CMD ["./start.sh"]
