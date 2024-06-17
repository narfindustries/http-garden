FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install wget && wget 'https://go.dev/dl/go1.22.1.linux-amd64.tar.gz' -O go.tgz && tar -C /usr/local -xzf go.tgz && rm go.tgz

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

WORKDIR /app/go
ARG APP_VERSION
RUN git pull && git checkout "$APP_VERSION" && cd src && export PATH="$PATH:/usr/local/go/bin" && ./all.bash
RUN rm -rf /usr/local/go && cp -r ./bin/* /bin && cp -r ./lib/* /lib

WORKDIR /app
ARG APP_SOURCE
COPY $APP_SOURCE .

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" "$APP_SOURCE"

RUN go build -o app "$APP_SOURCE"

CMD ["./app"]
