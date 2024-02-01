FROM http-garden-soil:latest

ARG APP_VERSION
RUN git clone 'https://github.com/civetweb/civetweb'
RUN cd /app/civetweb && git checkout $APP_VERSION && cd examples/rest && make -j$(nproc) && mkdir ../server

COPY ./server.c /app/civetweb/examples/server/

RUN cd /app/civetweb/examples/server && afl-cc -I../../include -fsanitize=address,undefined server.c -o server ../../libcivetweb.a

#CMD ["/app/civetweb/examples/server/server"]
