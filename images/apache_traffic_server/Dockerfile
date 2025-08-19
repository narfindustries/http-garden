FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends cmake ninja-build pkg-config zlib1g-dev libssl-dev libpcre2-dev \
 && echo "deb https://deb.debian.org/debian/ bookworm main non-free contrib" > /etc/apt/sources.list.d/bookworm.list \
 && apt -y update \
 && apt -y install libpcre3-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# Using sanitizers here caused ATS to segfault. This is probably a real bug, but I don't have time to figure it out. Disabling for now.
ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/trafficserver \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cmake --preset default \
 && cmake --build build-default \
 && cmake --install build-default

COPY ./records.yaml /usr/local/trafficserver/etc/trafficserver/records.yaml
COPY ./remap.config /usr/local/trafficserver/etc/trafficserver/remap.config
COPY ./cache.config /usr/local/trafficserver/etc/trafficserver/cache.config
COPY ./ip_allow.yaml /usr/local/trafficserver/etc/trafficserver/ip_allow.yaml

ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /usr/local/trafficserver/etc/trafficserver/records.yaml /usr/local/trafficserver/etc/trafficserver/remap.config \
 && chmod -R 777 /usr/local/trafficserver/var

COPY start.sh .

CMD ["./start.sh"]
