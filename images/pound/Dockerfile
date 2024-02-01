FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install perl autoconf automake libssl-dev && git clone "https://github.com/graygnuorg/pound"

ARG APP_VERSION

RUN cd /app/pound && git checkout $APP_VERSION && ./bootstrap && export CC='afl-cc' LDFLAGS='-fsanitize=address,undefined' CFLAGS='-fsanitize=address,undefined' && ./configure && make -j$(nproc) && make install

COPY pound.cfg /usr/local/etc/pound.cfg
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/etc/pound.cfg && mkdir -p /usr/local/var/run

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "pound", "-e"]
