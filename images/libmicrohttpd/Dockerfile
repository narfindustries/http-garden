FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends autoconf automake libtool-bin texinfo libapr1-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/libmicrohttpd \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./bootstrap \
 && ./configure \
 && make "-j$(nproc)" install

COPY garden_server.c .
RUN afl-cc -I/usr/local/include -Wall -Wextra -pedantic garden_server.c /usr/local/lib/libmicrohttpd.a $CFLAGS -o garden_server -lapr-1

CMD ["./garden_server"]
