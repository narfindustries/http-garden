FROM http-garden-soil:latest

ARG APP_REPO
RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends zlib1g-dev pkg-config cmake luarocks  && luarocks install base64 && git clone "$APP_REPO"

ARG APP_VERSION
RUN cd lwan && git checkout "$APP_VERSION" && mkdir build && cd build && cmake .. -DZLIB_LIBRARY=$(find /usr/lib -name 'libz.so') -DCMAKE_C_COMPILER='afl-cc' -DSANITIZER=address && make install

COPY lwan.conf /app

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "lwan", "-c", "/app/lwan.conf"]
