FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
  && apt -y install --no-install-recommends curl cmake g++ \
  && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

WORKDIR /app/pingora

COPY patch.diff .
ARG APP_VERSION
ARG APP_BRANCH
RUN git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && git apply /app/pingora/patch.diff \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 &&  sh -c ". ~/.cargo/env && cargo build"

ARG BACKEND
COPY garden_gateway.rs /app/pingora/pingora-proxy/examples
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/pingora/pingora-proxy/examples/garden_gateway.rs \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && sh -c ". ~/.cargo/env && cargo build --example garden_gateway"

CMD ["/app/pingora/target/debug/examples/garden_gateway"]
