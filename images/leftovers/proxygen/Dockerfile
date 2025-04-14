FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends sudo lsb-release cmake libboost-all-dev libdouble-conversion-dev libfast-float-dev libssl-dev libgoogle-glog-dev libsodium-dev gperf libapr1-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && cd proxygen \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cd proxygen \
 && ./build.sh \
 && ./install.sh

COPY EchoHandler.cpp /app

RUN "$CXX" $CXXFLAGS -o echo_server -I./proxygen/proxygen/_build/deps/include -I./proxygen/proxygen/_build/include EchoHandler.cpp -lglog -lgflags -lsodium -lssl -lcrypto -lz -levent -llzma -lsnappy -ldouble-conversion -llz4 -lboost_context -liberty -lapr-1 ./proxygen/proxygen/_build/lib/libproxygen.a ./proxygen/proxygen/_build/lib/libproxygenhttpserver.a ./proxygen/proxygen/_build/deps/lib/libfmt.a ./proxygen/proxygen/_build/deps/lib/libfolly.a ./proxygen/proxygen/_build/deps/lib/libwangle.a ./proxygen/proxygen/_build/deps/lib/libfizz.a ./proxygen/proxygen/_build/deps/lib/libzstd.a ./proxygen/proxygen/_build/deps/mvfst/build/quic/libmvfst_exception.a

CMD ["/app/echo_server"]
