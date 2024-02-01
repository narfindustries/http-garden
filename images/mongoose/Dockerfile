FROM http-garden-soil:latest

RUN git clone 'https://github.com/cesanta/mongoose'

ARG APP_VERSION
RUN cd /app/mongoose && git checkout $APP_VERSION

ARG SERVER_SOURCE
COPY $SERVER_SOURCE /app/mongoose/examples/http-server/main.c

RUN cd /app/mongoose/examples/http-server && make CC=afl-cc CFLAGS='-fsanitize=address,undefined' -j$(nproc) example

WORKDIR /app/mongoose

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "/app/mongoose/examples/http-server/example"]
