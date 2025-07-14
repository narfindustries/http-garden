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
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/etc/pound.cfg \
 && mkdir -p /usr/local/var/run

CMD ["pound", "-e"]
