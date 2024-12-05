FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends autoconf bison pkg-config libsqlite3-dev re2c

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd php-src && git pull && git checkout "$APP_VERSION" && ./buildconf && ./configure && make -j"$(nproc)" && make install

COPY ./index.php .
CMD ["php", "-S", "0.0.0.0:80", "index.php"]
