FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends autoconf automake libtool-bin texinfo libapr1-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/libmicrohttpd && git pull && git checkout "$APP_VERSION" && ./bootstrap && ./configure && CFLAGS='-g -fsanitize=address,undefined' LDFLAGS='-fsanitize=address,undefined' CC='afl-cc' make -j$(nproc) install

COPY garden_server.c .
RUN afl-cc -I/usr/local/include -Wall -Wextra -pedantic garden_server.c /usr/local/lib/libmicrohttpd.a -fsanitize=address,undefined -o garden_server -lapr-1

CMD ["./garden_server"]
