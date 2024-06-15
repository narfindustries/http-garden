FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install autoconf libtool-bin uncrustify texinfo && git clone "https://git.gnunet.org/libmicrohttpd.git"

ARG APP_VERSION
RUN cd /app/libmicrohttpd && git checkout $APP_VERSION && ./bootstrap && CC='afl-cc' CFLAGS='-fsanitize=address,undefined' ./configure && make -j$(nproc) && make install

COPY app.c /app/app.c
RUN afl-cc -fsanitize=address,undefined app.c /usr/local/lib/libmicrohttpd.a -o app

CMD ["/app/app"]
