FROM http-garden-soil:latest

ARG APP_VERSION
RUN git clone 'https://github.com/civetweb/civetweb'
RUN cd /app/civetweb && git checkout $APP_VERSION && make -j$(nproc) && make install-lib install-headers

COPY ./server.c /app/

RUN afl-cc -fsanitize=address,undefined -o server server.c /usr/local/lib/libcivetweb.a

CMD ["/app/server"]
