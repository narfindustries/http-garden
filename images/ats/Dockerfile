FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install libpcre2-dev luajit tcl-dev cmake pkg-config zlib1g-dev libssl-dev libpcre3-dev libcap-dev libhwloc-dev libncurses5-dev libcurl4-openssl-dev flex libunwind-dev libxml2-dev && git clone "https://github.com/apache/trafficserver"

ARG APP_VERSION
# We're not using UBSan and ASan here because ATS has too much UB, too deep. Segfaults.
RUN cd /app/trafficserver && git checkout $APP_VERSION && cmake -B build && cd build && make -j$(nproc) && make install

COPY ./records.yaml /usr/local/trafficserver/etc/trafficserver/records.yaml
COPY ./remap.config /usr/local/trafficserver/etc/trafficserver/remap.config
#COPY ./ip_allow.yaml /usr/local/trafficserver/etc/trafficserver/ip_allow.yaml

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/trafficserver/etc/trafficserver/records.yaml /usr/local/trafficserver/etc/trafficserver/remap.config

RUN chmod -R 777 /usr/local/trafficserver/var

CMD /usr/local/trafficserver/bin/traffic_server --httpport 80
