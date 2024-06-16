FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install wget golang

RUN git clone "https://github.com/valyala/fasthttp"

COPY app.go .

ARG APP_VERSION
RUN cd /app/fasthttp && git pull && git checkout "$APP_VERSION" && go install && mkdir examples/app && mv ../app.go examples/app

WORKDIR /app/fasthttp
CMD ["go", "run", "examples/app/app.go"]
