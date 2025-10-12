FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends curl \
 && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
 && . ~/.cargo/env \
 && rustup default nightly

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/hyper \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && . ~/.cargo/env \
 && cargo build --features=full

ARG HYPER_UTIL_REPO
ARG HYPER_UTIL_VERSION
ARG HYPER_UTIL_BRANCH
RUN git clone --recurse-submodules "$HYPER_UTIL_REPO"
RUN cd /app/hyper-util \
 && git pull origin "$HYPER_UTIL_BRANCH" \
 && git checkout "$HYPER_UTIL_VERSION" \
 && sed -i 's/hyper = .*/hyper = { path = "\/app\/hyper", features = ["full"] }/' Cargo.toml \
 && . ~/.cargo/env \
 && cargo build --features=full

COPY garden /app/garden
RUN cd /app/garden \
 && . ~/.cargo/env \
 && cargo build

CMD cd /app/garden \
 && . ~/.cargo/env \
 && cargo run
