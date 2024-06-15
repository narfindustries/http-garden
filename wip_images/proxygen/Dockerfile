FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && git clone "https://github.com/facebook/proxygen"

ARG APP_VERSION
RUN cd /app/proxygen && git checkout $APP_VERSION && sed -i 's/sudo //g' proxygen/build.sh && cd proxygen && ./build.sh

# This is gross, but I don't feel like using their build system the right way.
# TODO: Use ASAN and UBSan here
RUN rm -rf /app/proxygen/proxygen/httpserver/samples/echo && mkdir /app/proxygen/proxygen/httpserver/samples/echo
COPY EchoHandler.cpp /app/proxygen/proxygen/httpserver/samples/echo
COPY EchoHandler.h /app/proxygen/proxygen/httpserver/samples/echo
COPY EchoServer.cpp /app/proxygen/proxygen/httpserver/samples/echo

RUN cd /app/proxygen/proxygen && ./build.sh && ./install.sh

CMD ["/app/proxygen/proxygen/_build/bin/proxygen_echo"]
