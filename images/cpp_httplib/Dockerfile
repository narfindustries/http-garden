FROM http-garden-soil:latest

ARG APP_REPO
RUN apt -y update && apt -y upgrade && apt -y install meson ninja-build cmake pkg-config libbrotli-dev libssl-dev libapr1-dev && git clone "$APP_REPO"

ARG APP_VERSION
RUN cd /app/cpp-httplib && git pull && git checkout "$APP_VERSION" && meson setup build && cd build && ninja install

COPY server.cpp .

RUN afl-c++ -fsanitize=address,undefined -g server.cpp -o server -lapr-1

CMD ["./server"]
