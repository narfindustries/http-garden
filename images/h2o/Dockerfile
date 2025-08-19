FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends cmake zlib1g-dev libbrotli-dev libcap-dev libssl-dev "linux-headers-$(dpkg --print-architecture)" pkg-config libwslay-dev libuv1-dev ruby-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH

ARG PARSER_VERSION
ARG PARSER_REPO
RUN cd h2o \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cd deps \
 && rm -rf picohttpparser \
 && git clone --recurse-submodules "$PARSER_REPO" \
 && cd picohttpparser \
 && git pull origin "$PARSER_BRANCH" \
 && git checkout "$PARSER_VERSION" \
 && cd /app/h2o \
 && mkdir build \
 && cd build \
 && cmake -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" -DCMAKE_C_FLAGS="$CFLAGS" -DCMAKE_CXX_FLAGS="$CXXFLAGS" -DCMAKE_LD_FLAGS="$LDFLAGS" -DCMAKE_BUILD_TYPE=Debug -DWITH_MRUBY=on -DCMAKE_SYSTEM_LIBRARY_PATH="/usr/lib/$(uname -m)-linux-gnu/" .. \
 && make "-j$(nproc)" \
 && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/h2o.conf

ARG START_SCRIPT
COPY $START_SCRIPT ./start.sh

ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /app/h2o.conf

CMD ["./start.sh"]
