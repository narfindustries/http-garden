FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends cmake zlib1g-dev libbrotli-dev libcap-dev libssl-dev linux-headers-amd64 pkg-config libwslay-dev libuv1-dev ruby-dev

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
 && cmake -DCMAKE_C_COMPILER='clang' -DCMAKE_CXX_COMPILER='clang++' -DCMAKE_BUILD_TYPE=Debug -DWITH_MRUBY=on -DCMAKE_SYSTEM_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/' .. \
 && make "-j$(nproc)" \
 && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/h2o.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/h2o.conf

CMD ["h2o", "-c", "/app/h2o.conf"]
