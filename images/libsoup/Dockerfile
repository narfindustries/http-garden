FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends meson cmake pkg-config libglib2.0-dev libnghttp2-dev libsqlite3-dev libpsl-dev libbrotli-dev glib-networking glib-networking

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

COPY server.c /app/libsoup/examples/simple-httpd.c

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/libsoup \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && mkdir build \
 && cd build \
 && meson setup .. --default-library static \
 && ninja install

CMD "/app/libsoup/build/examples/simple-httpd"
