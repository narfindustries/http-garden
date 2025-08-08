FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends curl \
 && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN sh -c ". ~/.cargo/env && cd /app/hyper && git pull origin \"$APP_BRANCH\" && git checkout \"$APP_VERSION\" && sed -i 's/\[dependencies\]/[dependencies]\nbase64 = \"0.21.5\"/' /app/hyper/Cargo.toml && cargo build"

COPY garden.rs /app/hyper/examples


RUN sh -c ". ~/.cargo/env && cd hyper && cargo build --features=full --example=garden"

WORKDIR /app/hyper
CMD "sh" "-c" ". ~/.cargo/env && cargo run --features=full --example=garden"
