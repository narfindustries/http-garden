FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install cmake

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/libevent && git pull && git checkout "$APP_VERSION" && cmake . -DCMAKE_C_FLAGS='-fsanitize=address,undefined' -DCMAKE_C_COMPILER='afl-cc' && make -j`nproc`

COPY ./http-garden.c /app/libevent/sample/http-garden.c
RUN cd /app/libevent && afl-cc -fsanitize=address,undefined -Wall -Wextra -Iinclude sample/http-garden.c lib/libevent.a -o http-garden

ENV AFL_DEBUG=1
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "/app/libevent/http-garden"]
