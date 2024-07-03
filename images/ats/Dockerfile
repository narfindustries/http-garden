FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install libpcre2-dev luajit tcl-dev cmake pkg-config zlib1g-dev libssl-dev libpcre3-dev libcap-dev libhwloc-dev libncurses5-dev libcurl4-openssl-dev flex libunwind-dev libxml2-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
# We're not using UBSan and ASan here because ATS has too much UB, too deep. Segfaults.
RUN cd /app/trafficserver && git pull && git checkout "$APP_VERSION" && cmake -B build && cd build && make -j$(nproc) && make install

ARG RECORDS_YAML
COPY ./records.yaml /usr/local/trafficserver/etc/trafficserver/records.yaml

ARG REMAP_CONFIG
COPY ./remap.config /usr/local/trafficserver/etc/trafficserver/remap.config

ARG CACHE_CONFIG
COPY ./cache.config /usr/local/trafficserver/etc/trafficserver/cache.config

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/trafficserver/etc/trafficserver/records.yaml /usr/local/trafficserver/etc/trafficserver/remap.config

RUN chmod -R 777 /usr/local/trafficserver/var

CMD /usr/local/trafficserver/bin/traffic_server --httpport 80
