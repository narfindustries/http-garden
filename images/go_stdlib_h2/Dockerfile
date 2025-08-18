FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends golang

ARG APP_REPO
RUN git clone "$APP_REPO"

ARG APP_BRANCH
ARG APP_VERSION
RUN cd net \
    && git pull origin "$APP_BRANCH" \
    && git checkout "$APP_VERSION"

ARG APP_SOURCE
COPY $APP_SOURCE .
RUN go mod init app \
    && go mod edit -replace=golang.org/x/net=./net \
    && go mod edit -require=golang.org/x/net@v0.0.0 \
    && go mod tidy \
    && go build -o app "$APP_SOURCE"

CMD ["./app"]
