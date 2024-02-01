FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install wget && wget 'https://go.dev/dl/go1.21.5.linux-amd64.tar.gz' && git clone https://github.com/golang/go

RUN tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && rm go1.21.5.linux-amd64.tar.gz

WORKDIR /app/go
ARG APP_VERSION
RUN git checkout $APP_VERSION && cd src && export PATH="$PATH:/usr/local/go/bin" && ./all.bash
RUN rm -rf /usr/local/go && cp -r ./bin/* /bin && cp -r ./lib/* /lib

WORKDIR /app
COPY app.go .
RUN go build app.go

CMD ["./app"]
