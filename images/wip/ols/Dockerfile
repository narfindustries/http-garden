FROM debian:bullseye-slim

WORKDIR /app

RUN apt -y update && apt -y install wget curl php-fpm

ARG APP_VERSION
RUN wget "https://github.com/litespeedtech/openlitespeed/releases/download/v${APP_VERSION}/openlitespeed-${APP_VERSION}-x86_64-linux.tgz" && tar xf openlitespeed*.tgz

RUN cd /app/openlitespeed && ./install.sh

RUN mkdir /run/php && sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/7.4/fpm/pool.d/www.conf

# RUN rm -rf /usr/local/lsws/conf/ \
#  && mkdir /usr/local/lsws/conf \
#  && mkdir -p /usr/local/lsws/vhost_root
# COPY httpd_config.conf /usr/local/lsws/conf/
# COPY mime.properties /usr/local/lsws/conf/
# COPY vhconf.conf /usr/local/lsws/conf/vhosts/vhost/
# COPY index.php /usr/local/lsws/vhost_root/
# RUN chown -R lsadm:nogroup /usr/local/lsws/conf

RUN apt -y install ncat

CMD php-fpm7.4 \
 && /usr/local/lsws/bin/openlitespeed -d
