FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends curl cmake \
 && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
 && . ~/.cargo/env \
 && rustup default nightly

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/pingora \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && . ~/.cargo/env \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && cargo build

COPY garden /app/garden
RUN cd /app/garden \
 && . ~/.cargo/env \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && cargo fix --lib -p pingora-error --allow-no-vcs \
 && cargo fix --lib -p pingora-core --allow-no-vcs \
 && cargo build

CMD cd /app/garden \
 && . ~/.cargo/env \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && cargo run
