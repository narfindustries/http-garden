FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install curl && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && git clone 'https://github.com/hyperium/hyper'

WORKDIR /app/hyper
ARG APP_VERSION
RUN sh -c ". ~/.cargo/env && git pull && git checkout \"$APP_VERSION\" && sed -i 's/\[dependencies\]/[dependencies]\nbase64 = \"0.21.5\"/' /app/hyper/Cargo.toml && cargo build"

COPY garden.rs /app/hyper/examples

RUN sh -c ". ~/.cargo/env && cargo build --features=full --example=garden"

CMD ["sh", "-c", ". ~/.cargo/env && cargo run --features=full --example=garden"]
