FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends wget golang

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

COPY app.go .

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/fasthttp \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && go install \
 && mkdir examples/app \
 && mv ../app.go examples/app

WORKDIR /app/fasthttp
CMD ["go", "run", "examples/app/app.go"]
