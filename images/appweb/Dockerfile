FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install libssl-dev libapr1-dev

ARG APP_REPO
ARG MAKEME_REPO
RUN git clone --recurse-submodules "$APP_REPO" \
 && git clone --recurse-submodules "$MAKEME_REPO"


ENV LD_LIBRARY_PATH=/app/makeme/build/linux-x64-default/bin:/app/appweb/build/linux-x64-default/bin/appweb

# We don't use -j$(nproc) in the build here because there are race conditions in the makefiles
ARG MAKEME_VERSION
ARG MAKEME_BRANCH
RUN cd /app/makeme \
 && git pull origin "$MAKEME_BRANCH" \
 && git checkout "$MAKEME_VERSION" \
 && git submodule update --init --recursive \
 && make \
 && make install

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/appweb \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && git submodule update --init --recursive \
 && make ME_COM_FAST=1 ME_COM_PROXY=1 \
 && make install

ENV LD_LIBRARY_PATH=/usr/local/lib/appweb/latest/bin:/usr/local/lib/makeme/latest/bin

COPY server.c .
RUN "$CC" $CFLAGS -I/app/appweb/build/linux-x64-default/inc server.c -shared -o libmod_echo.so -L/app/appweb/build/linux-x64-default/bin -lappweb -lmpr -lhttp -lapr-1

ARG CONFIG_FILE
COPY $CONFIG_FILE ./appweb.conf
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" appweb.conf

CMD ["appweb"]
