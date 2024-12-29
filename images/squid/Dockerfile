FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends automake autoconf libtool libtool-bin libltdl-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# Squid just keeps crashing with sanitizers and AFL. Disabling it all for now.

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/squid \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && ./bootstrap.sh \
 && ./configure --disable-esi \
 && make "-j$(nproc)" \
 && make install

COPY ./squid.conf /usr/local/squid/etc
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/squid/etc/squid.conf \
 && useradd squid \
 && chown -R squid:squid /usr/local/squid

CMD rm -f /usr/local/squid/var/run/squid.pid \
 && /usr/local/squid/sbin/squid --foreground
