FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends libtool libc-ares-dev libevent-dev libjansson-dev libsystemd-dev libjemalloc-dev libev-dev

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

ARG PARAMS
ENV PARAMS=$PARAMS

CMD /app/nghttp2/src/nghttpx --no-add-x-forwarded-proto --no-strip-incoming-x-forwarded-proto --no-via --no-strip-incoming-early-data --no-location-rewrite --no-server-rewrite --insecure '--frontend=0.0.0.0,80;no-tls' "--backend=$BACKEND,80$PARAMS"
