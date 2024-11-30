FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends npm

ARG PARSER_REPO
RUN git clone --recurse-submodules "$PARSER_REPO"

ARG PARSER_VERSION
RUN cd /app/llhttp && git pull && git checkout "$PARSER_VERSION" && npm install && make -j`nproc`

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/node && git pull && git checkout "$APP_VERSION" && cp /app/llhttp/src/native/api.c /app/llhttp/src/native/http.c /app/llhttp/build/c/llhttp.c deps/llhttp/src && cp /app/llhttp/build/llhttp.h deps/llhttp/include && ./configure && make -j$(nproc)

ARG SCRIPT
COPY $SCRIPT /app/app.js

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/app.js

CMD ["/app/node/node", "app.js"]
