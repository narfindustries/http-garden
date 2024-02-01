FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install cmake protobuf-compiler curl && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && git clone 'https://github.com/denoland/deno'

ARG APP_VERSION
RUN cd /app/deno && git checkout $APP_VERSION && bash -c ". /root/.cargo/env && cargo build"

COPY app.js /app

CMD ["/app/deno/target/debug/deno", "run", "--allow-net", "/app/app.js"]
