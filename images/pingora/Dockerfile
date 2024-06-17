FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install curl cmake g++ && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

WORKDIR /app/pingora

ARG APP_VERSION
RUN git pull && git checkout "$APP_VERSION"

RUN sh -c ". ~/.cargo/env && cargo build"

ARG BACKEND
COPY garden_gateway.rs /app/pingora/pingora-proxy/examples
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/pingora/pingora-proxy/examples/garden_gateway.rs && sh -c ". ~/.cargo/env && cargo build --example garden_gateway"

CMD ["/app/pingora/target/debug/examples/garden_gateway"]
