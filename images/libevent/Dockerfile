FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends cmake

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/libevent \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cmake . \
 && make "-j$(nproc)"

COPY ./http-garden.c /app/libevent/sample/http-garden.c
RUN cd /app/libevent \
 && $CC $CFLAGS -Wall -Wextra -Iinclude sample/http-garden.c lib/libevent.a -o http-garden

CMD "/app/libevent/http-garden"
