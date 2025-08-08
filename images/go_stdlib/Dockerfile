FROM http-garden-soil:latest

ARG GO_BOOTSTRAP_VERSION
RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends wget \
 && wget "https://go.dev/dl/go$GO_BOOTSTRAP_VERSION.linux-$(dpkg --print-architecture).tar.gz" -O go.tgz \
 && tar -C /usr/local -xzf go.tgz \
 && rm go.tgz

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/go \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cd src \
 && export PATH="$PATH:/usr/local/go/bin" \
 && ./make.bash \
 && rm -rf /usr/local/go \
 && cp -r /app/go/bin/* /bin \
 && cp -r /app/go/lib/* /lib

ARG APP_SOURCE
COPY $APP_SOURCE .

ARG BACKEND_HOST
ARG BACKEND_PORT
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" "$APP_SOURCE" \
 && go build -o app "$APP_SOURCE"

CMD "./app"
