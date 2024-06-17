FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install cmake protobuf-compiler curl && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/deno && git pull && git checkout "$APP_VERSION" && bash -c ". /root/.cargo/env && cargo build"

COPY app.js /app

CMD ["/app/deno/target/debug/deno", "run", "--allow-net", "/app/app.js"]
