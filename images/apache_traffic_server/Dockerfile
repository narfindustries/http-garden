FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends libpcre2-dev luajit tcl-dev cmake pkg-config zlib1g-dev libssl-dev libcap-dev libhwloc-dev libncurses5-dev libcurl4-openssl-dev flex libunwind-dev libxml2-dev

RUN echo "deb http://deb.debian.org/debian/ unstable main non-free contrib" > /etc/apt/sources.list.d/sid.list && apt -y update && apt -y install libpcre3-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
# We're not using UBSan and ASan here because ATS has too much UB, too deep. Segfaults.
RUN cd /app/trafficserver && git pull && git checkout "$APP_VERSION" && cmake -B build && cd build && make -j$(nproc) && make install

COPY ./records.yaml /usr/local/trafficserver/etc/trafficserver/records.yaml

COPY ./remap.config /usr/local/trafficserver/etc/trafficserver/remap.config

COPY ./cache.config /usr/local/trafficserver/etc/trafficserver/cache.config

COPY ./ip_allow.yaml /usr/local/trafficserver/etc/trafficserver/ip_allow.yaml

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/trafficserver/etc/trafficserver/records.yaml /usr/local/trafficserver/etc/trafficserver/remap.config

RUN chmod -R 777 /usr/local/var/trafficserver /usr/local/trafficserver/var

CMD /usr/local/trafficserver/bin/traffic_server --httpport 80
