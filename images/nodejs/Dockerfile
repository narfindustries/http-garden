FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install npm && git clone "https://github.com/nodejs/node" && git clone "https://github.com/nodejs/llhttp"

ARG LLHTTP_VERSION
RUN cd /app/llhttp && git checkout $LLHTTP_VERSION && npm install && make -j`nproc`

ARG APP_VERSION
RUN cd /app/node && git checkout $APP_VERSION && cp /app/llhttp/src/native/api.c /app/llhttp/src/native/http.c /app/llhttp/build/c/llhttp.c deps/llhttp/src && cp /app/llhttp/build/llhttp.h deps/llhttp/include && ./configure && make -j$(nproc)

COPY app.js /app
CMD ["/app/node/node", "app.js"]
