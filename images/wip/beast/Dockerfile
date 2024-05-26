FROM http-garden-soil:latest

RUN git clone --recursive https://github.com/boostorg/boost.git
ARG APP_VERSION
RUN cd boost/libs/beast && git checkout $APP_VERSION && cd ../.. && ./bootstrap.sh && ./b2 headers install

COPY ./http_server.cpp /app
RUN afl-c++ http_server.cpp -o server

CMD exec afl-showmap -o /tmp/trace -t 2147483647 -- ./server 0.0.0.0 80
