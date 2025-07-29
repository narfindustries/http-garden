FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends pkg-config cmake lua5.4 libjson-c-dev libssl-dev luarocks \
 && luarocks-5.1 install base64

ARG UCODE_REPO
RUN git clone --recurse-submodules "$UCODE_REPO"
ARG UCODE_VERSION
ARG UCODE_BRANCH
RUN cd /app/ucode \
 && git pull origin "$UCODE_BRANCH" \
 && git checkout "$UCODE_VERSION" \
 && cmake . -DCMAKE_SYSTEM_LIBRARY_PATH="/usr/lib/$(uname -m)-linux-gnu/" \
 && make "-j$(nproc)" \
 && make install

ARG LIBUBOX_REPO
ARG LIBUBOX_BRANCH
RUN git clone --recurse-submodules "$LIBUBOX_REPO"
ARG LIBUBOX_VERSION
RUN cd /app/libubox \
 && git pull origin "$LIBUBOX_BRANCH" \
 && git checkout "$LIBUBOX_VERSION" \
 && cmake . -DCMAKE_SYSTEM_LIBRARY_PATH="/usr/lib/$(uname -m)-linux-gnu/" \
 && make "-j$(nproc)" \
 && make install

ARG LIBUBUS_REPO
ARG LIBUBUS_BRANCH
RUN git clone --recurse-submodules "$LIBUBUS_REPO"
ARG LIBUBUS_VERSION
RUN cd /app/ubus \
 && git pull origin "$LIBUBUS_BRANCH" \
 && git checkout "$LIBUBUS_VERSION" \
 && cmake . -DCMAKE_SYSTEM_LIBRARY_PATH="/usr/lib/$(uname -m)-linux-gnu/" \
 && make "-j$(nproc)" \
 && make install

ARG USTREAM_SSL_REPO
RUN git clone --recurse-submodules "$USTREAM_SSL_REPO"
ARG USTREAM_SSL_VERSION
ARG USTREAM_SSL_BRANCH
RUN cd /app/ustream-ssl \
 && git pull origin "$USTREAM_SSL_BRANCH" \
 && git checkout "$USTREAM_SSL_VERSION" \
 && cmake . -DCMAKE_SYSTEM_LIBRARY_PATH="/usr/lib/$(uname -m)-linux-gnu/" \
 && make "-j$(nproc)" \
 && make install

RUN cp /usr/local/lib/libucode.so /usr/lib

ARG APP_REPO
ARG APP_BRANCH
RUN git clone --recurse-submodules "$APP_REPO"
ARG APP_VERSION
RUN cd /app/uhttpd \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cmake . -DCMAKE_SYSTEM_LIBRARY_PATH="/usr/lib/$(uname -m)-linux-gnu/" \
 && make "-j$(nproc)" \
 && make install

RUN cp /usr/local/lib/*.so /usr/lib

COPY server.lua .
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "uhttpd", "-f", "-p", "0.0.0.0:80", "-l/", "-L/app/server.lua", "-T", "1"]
