FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install wget && wget 'https://go.dev/dl/go1.21.5.linux-amd64.tar.gz' && git clone https://github.com/golang/go

RUN tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && rm go1.21.5.linux-amd64.tar.gz

WORKDIR /app/go
RUN cd src && export PATH="$PATH:/usr/local/go/bin" && ./all.bash
RUN rm -rf /usr/local/go && cp -r ./bin/* /bin && cp -r ./lib/* /lib

WORKDIR /app

RUN apt -y install wget php-fpm && git clone "https://github.com/caddyserver/caddy" && mkdir xcaddy && cd xcaddy && wget "https://github.com/caddyserver/xcaddy/releases/download/v0.3.4/xcaddy_0.3.4_linux_amd64.tar.gz" -O xcaddy.tgz && tar xf xcaddy.tgz

ARG APP_VERSION
RUN cp /app/xcaddy/xcaddy /usr/local/bin && cd /app/caddy && git checkout $APP_VERSION && xcaddy build

RUN sed -i 's/^listen = \/run\/php\/.*/listen = 127.0.0.1:9000/' /etc/php/8.2/fpm/pool.d/www.conf

COPY ./Caddyfile /app/caddy/Caddyfile
COPY ./index.php /app/index.php

ARG BACKEND
ENV BACKEND=$BACKEND

CMD exec sh -c "test -z $BACKEND && ( \
    php-fpm8.2 && exec /app/caddy/caddy run --config /app/caddy/Caddyfile \
) || ( \
    exec /app/caddy/caddy reverse-proxy --from :80 --to ${BACKEND}:80 \
)"
