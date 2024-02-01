FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install tcl-dev cmake pkg-config zlib1g-dev libssl-dev libpcre3-dev libcap-dev libhwloc-dev libncurses5-dev libcurl4-openssl-dev flex libunwind-dev libxml2-dev && git clone "https://github.com/apache/trafficserver"

COPY patch.diff /app/trafficserver

ARG APP_VERSION
# We're not using UBSan and ASan here because ATS has too much UB, too deep. Segfaults.
RUN cd /app/trafficserver && git checkout $APP_VERSION && patch -p1 < patch.diff && cmake -B build -DCMAKE_C_COMPILER='afl-cc' -DCMAKE_CXX_COMPILER='afl-c++' && cd build && make -j$(nproc) && make install

COPY ./records.yaml /usr/local/trafficserver/etc/trafficserver/records.yaml
COPY ./remap.config /usr/local/trafficserver/etc/trafficserver/remap.config

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/trafficserver/etc/trafficserver/records.yaml /usr/local/trafficserver/etc/trafficserver/remap.config

RUN chmod -R 777 /usr/local/trafficserver/var

CMD export AFL_MAP_SIZE="$(AFL_DEBUG=1 afl-showmap -o /dev/null  -t 2147483647 -- /usr/local/trafficserver/bin/traffic_server --httpport 80 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}')" \
 && exec afl-showmap -o /tmp/trace -t 2147483647 -- /usr/local/trafficserver/bin/traffic_server --httpport 80
