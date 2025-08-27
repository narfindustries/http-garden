FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends perl autoconf automake libssl-dev texinfo libtool

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/pound \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./bootstrap \
 && ./configure \
 && make "-j$(nproc)" \
 && make install

COPY pound.cfg /usr/local/etc/pound.cfg
ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /usr/local/etc/pound.cfg \
 && mkdir -p /usr/local/var/run

COPY start.sh .

CMD python3 /tools/echo_server.py 127.0.0.1 "$((0xdafe))" & pound -e
