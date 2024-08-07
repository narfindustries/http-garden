FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends cmake zlib1g-dev libbrotli-dev libcap-dev libssl-dev perl linux-headers-amd64 ruby rake pkg-config

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG PARSER_VERSION
ARG PARSER_REPO
RUN cd h2o && git pull && git checkout "$APP_VERSION" && cd deps && rm -rf picohttpparser && git clone --recurse-submodules "$PARSER_REPO" && cd picohttpparser && git pull && git checkout "$PARSER_VERSION"
RUN cd h2o && mkdir build && cd build && cmake -DWITH_MRUBY=on -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_CXX_COMPILER='afl-c++' -DCMAKE_C_CFLAGS='-fsanitize=address,undefined' -DCMAKE_CXX_FLAGS='-fsanitize=address,undefined' -DCMAKE_LD_FLAGS='-fsanitize=address,undefined' -DCMAKE_SYSTEM_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu/' .. && make -j$(nproc) && make install

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/h2o.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/h2o.conf

RUN afl-showmap -o /dev/null -t 2147483647 -- h2o -c /app/h2o.conf 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}' > afl_map_size

CMD export AFL_MAP_SIZE="$(cat afl_map_size)" \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- h2o -c /app/h2o.conf
