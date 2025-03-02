FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends wget \
 && wget 'https://go.dev/dl/go1.24.0.linux-amd64.tar.gz' -O go.tgz \
 && tar -C /usr/local -xzf go.tgz \
 && rm go.tgz

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

COPY 0001-remove-broken-test.patch .

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/go \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cd src \
 && export PATH="$PATH:/usr/local/go/bin" \
 && git apply /app/0001-remove-broken-test.patch \
 && ./all.bash \
 && rm -rf /usr/local/go \
 && cp -r /app/go/bin/* /bin \
 && cp -r /app/go/lib/* /lib

ARG APP_SOURCE
COPY $APP_SOURCE .

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" "$APP_SOURCE" \
 && go build -o app "$APP_SOURCE"

CMD ["./app"]
