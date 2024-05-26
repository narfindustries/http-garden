FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install wget && wget 'https://go.dev/dl/go1.21.5.linux-amd64.tar.gz' && git clone https://github.com/golang/go

RUN tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && rm go1.21.5.linux-amd64.tar.gz

WORKDIR /app/go
RUN cd src && export PATH="$PATH:/usr/local/go/bin" && ./all.bash
RUN rm -rf /usr/local/go && cp -r ./bin/* /bin && cp -r ./lib/* /lib

WORKDIR /app

RUN git clone "https://github.com/valyala/fasthttp"

COPY app.go .

ARG APP_VERSION
RUN cd /app/fasthttp && git checkout $APP_VERSION && go install && mkdir examples/app && mv ../app.go examples/app

WORKDIR /app/fasthttp
CMD ["go", "run", "examples/app/app.go"]
