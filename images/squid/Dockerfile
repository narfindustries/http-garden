FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends automake autoconf libtool libtool-bin libltdl-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/squid \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./bootstrap.sh \
 && ./configure --disable-esi \
 && make "-j$(nproc)" \
 && make install

COPY ./squid.conf /usr/local/squid/etc
ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /usr/local/squid/etc/squid.conf \
 && useradd squid \
 && chown -R squid:squid /usr/local/squid

CMD python3 /tools/echo_server.py --host-url "http://127.0.0.1:$((0xdafe))" --pcap-url "http://0.0.0.0:$((0xda1e))" & rm -f /usr/local/squid/var/run/squid.pid && /usr/local/squid/sbin/squid --foreground
