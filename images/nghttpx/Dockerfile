FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends libtool libc-ares-dev libevent-dev libjansson-dev libsystemd-dev libjemalloc-dev libev-dev

# Debian Trixie's ngtcp2 is too old, so we need to build it ourselves.
ARG NGTCP2_REPO
RUN git clone --recurse-submodules "$NGTCP2_REPO"
ARG NGTCP2_VERSION
ARG NGTCP2_BRANCH
RUN cd ngtcp2 \
 && autoreconf -fi \
 && ./configure \
 && make "-j$(nproc)"

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd nghttp2 \
 && autoreconf -fi \
 && ./configure --enable-app \
 && make "-j$(nproc)"

ARG BACKEND
ENV BACKEND=$BACKEND
CMD /app/nghttp2/src/nghttpx --no-add-x-forwarded-proto --no-strip-incoming-x-forwarded-proto --no-via --no-strip-incoming-early-data --no-location-rewrite --no-server-rewrite --insecure --frontend=0.0.0.0,80\;no-tls --backend=$BACKEND',80;;proto=h2'
