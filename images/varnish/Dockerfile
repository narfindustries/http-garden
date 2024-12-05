FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends python3-docutils python3-sphinx autoconf automake libedit-dev libtool linux-headers-amd64 libpcre2-dev pkg-config

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd varnish-cache && git pull && git checkout "$APP_VERSION" && ./autogen.sh && ./configure CC='clang' && make -j"$(nproc)" && make install

COPY ./config.vcl /app/config.vcl

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/config.vcl

CMD ["/app/varnish-cache/bin/varnishd/varnishd", "-F", "-f", "/app/config.vcl", "-a", "http=:80,HTTP"]
