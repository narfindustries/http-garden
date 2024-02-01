FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install pkg-config cmake lua5.4 libjson-c-dev libssl-dev luarocks && git clone 'https://git.openwrt.org/project/libubox.git' && git clone 'https://git.openwrt.org/project/ustream-ssl.git' && git clone 'https://git.openwrt.org/project/ubus.git' && git clone 'https://git.openwrt.org/project/uhttpd.git' && git clone 'https://github.com/jow-/ucode' && luarocks-5.1 install base64

RUN cd /app/ucode && sed -i 's/static/\/\/static/' /app/ucode/json-c-compat.h && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_C_FLAGS='-fsanitize=address,undefined' && make -j$(nproc) && make install
RUN cd /app/libubox && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_C_FLAGS='-fsanitize=address,undefined' && make -j$(nproc) && make install
RUN cd /app/ubus && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_C_FLAGS='-fsanitize=address,undefined' && make -j$(nproc) && make install
RUN cd /app/ustream-ssl && sed -i 's/SET(CMAKE_SHARED_LINKER_FLAGS "-Wl,--no-undefined")//' CMakeLists.txt && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_C_FLAGS='-fsanitize=address,undefined' && make -j$(nproc) && make install

RUN cp /usr/local/lib/*.so /lib

ARG APP_VERSION
RUN cd /app/uhttpd && git checkout $APP_VERSION && cmake . -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_C_FLAGS='-fsanitize=address,undefined' && make -j$(nproc) && make install

RUN cp /usr/local/lib/*.so /lib

COPY server.lua .
ENV AFL_PRELOAD="/lib/uhttpd_lua.so"
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "uhttpd", "-f", "-p", "0.0.0.0:80", "-l/", "-L/app/server.lua", "-T", "1"]
