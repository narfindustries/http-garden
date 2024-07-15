FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends autoconf libtool automake pkg-config libssl-dev libev-dev zlib1g-dev libc-ares-dev libngtcp2-dev libsystemd-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

WORKDIR /app/nghttp2

# We're not building with afl here because it was causing symbol lookup errors for nghttp2's (not afl's) symbols.
ARG APP_VERSION
RUN git pull && git checkout "$APP_VERSION" && autoreconf -i && automake && autoconf && ./configure --enable-app CFLAGS='-fsanitize=address,undefined' LDFLAGS='-fsanitize=address,undefined' CXXFLAGS='-fsanitize=address,undefined' && make -j$(nproc) install

ARG BACKEND
ENV BACKEND=$BACKEND

#ENV LD_LIBRARY_PATH=/usr/local/lib
CMD exec nghttpx --backend="$BACKEND",80 '--frontend=*,80;no-tls'
