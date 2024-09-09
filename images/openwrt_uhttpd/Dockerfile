FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends pkg-config cmake lua5.4 libjson-c-dev libssl-dev luarocks && luarocks-5.1 install base64

ARG UCODE_REPO
RUN git clone --recurse-submodules "$UCODE_REPO"
ARG UCODE_VERSION
RUN cd /app/ucode && git pull && git checkout "$UCODE_VERSION" && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_SYSTEM_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/' -DCMAKE_C_FLAGS='-g -fsanitize=address,undefined' && make -j$(nproc) && make install

ARG LIBUBOX_REPO
RUN git clone --recurse-submodules "$LIBUBOX_REPO"
ARG LIBUBOX_VERSION
RUN cd /app/libubox && git pull && git checkout "$LIBUBOX_VERSION" && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_SYSTEM_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/' -DCMAKE_C_FLAGS='-g -fsanitize=address,undefined' && make -j$(nproc) && make install

ARG LIBUBUS_REPO
RUN git clone --recurse-submodules "$LIBUBUS_REPO"
ARG LIBUBUS_VERSION
RUN cd /app/ubus && git pull && git checkout "$LIBUBUS_VERSION" && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_SYSTEM_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/' -DCMAKE_C_FLAGS='-g -fsanitize=address,undefined' && make -j$(nproc) && make install

ARG USTREAM_SSL_REPO
RUN git clone --recurse-submodules "$USTREAM_SSL_REPO"
ARG USTREAM_SSL_VERSION
RUN cd /app/ustream-ssl && git pull && git checkout "$USTREAM_SSL_VERSION" && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_SYSTEM_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/' -DCMAKE_C_FLAGS='-g -fsanitize=address,undefined' && make -j"$(nproc)" && make install

RUN cp /usr/local/lib/libucode.so /usr/lib

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"
ARG APP_VERSION
RUN cd /app/uhttpd && git pull  && git checkout "$APP_VERSION" && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_SYSTEM_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/' -DCMAKE_C_FLAGS='-g -fsanitize=address,undefined' && make -j"$(nproc)" && make install

RUN cp /usr/local/lib/*.so /usr/lib

COPY server.lua .
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "uhttpd", "-f", "-p", "0.0.0.0:80", "-l/", "-L/app/server.lua", "-T", "1"]
