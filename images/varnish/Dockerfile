FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends python3-docutils python3-sphinx autoconf automake libedit-dev libtool linux-headers-amd64 libpcre2-dev pkg-config

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

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/config.vcl

# Disable strict initialization order checking and leak detection
ENV ASAN_OPTIONS='strict_string_checks=1:detect_stack_use_after_return=1:check_initialization_order=1:detect_leaks=0'

CMD ["/app/varnish-cache/bin/varnishd/varnishd", "-F", "-f", "/app/config.vcl", "-a", "http=:80,HTTP"]
