FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends npm

ARG PARSER_REPO
RUN git clone --recurse-submodules "$PARSER_REPO"

ARG PARSER_VERSION
ARG PARSER_BRANCH
RUN cd /app/llhttp \
 && git pull origin "$PARSER_BRANCH" \
 && git checkout "$PARSER_VERSION" \
 && npm install \
 && make "-j$(nproc)"

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/node \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cp /app/llhttp/src/native/api.c /app/llhttp/src/native/http.c /app/llhttp/build/c/llhttp.c deps/llhttp/src \
 && cp /app/llhttp/build/llhttp.h deps/llhttp/include \
 && ./configure \
 && make "-j$(nproc)"

COPY app.js /app/app.js

CMD ["/app/node/node", "app.js"]
