FROM http-garden-soil:latest

# quic-go doesn't build with Go 1.21 yet, so build with the one from the repos instead

RUN apt -y update && apt -y upgrade && apt -y install golang python3-setuptools && git clone "https://github.com/traefik/traefik"

WORKDIR /app/traefik
ARG APP_VERSION
RUN git checkout $APP_VERSION && go build ./cmd/traefik && cp ./traefik /bin

WORKDIR /app
COPY dynamic_config.yml .
COPY traefik.yml .
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" dynamic_config.yml

CMD ["traefik"]
