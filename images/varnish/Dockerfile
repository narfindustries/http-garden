FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends python3-docutils python3-sphinx autoconf automake libedit-dev libtool "linux-headers-$(dpkg --print-architecture)" libpcre2-dev pkg-config

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd varnish-cache \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./autogen.sh \
 && ./configure CC='clang' \
 && make "-j$(nproc)" \
 && make install

COPY ./config.vcl /app/config.vcl

ARG BACKEND_HOST
ARG BACKEND_PORT
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /app/config.vcl

CMD exec /app/varnish-cache/bin/varnishd/varnishd -F -f /app/config.vcl -a http=:80,HTTP
