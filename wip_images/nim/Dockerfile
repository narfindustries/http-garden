FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && git clone 'https://github.com/nim-lang/Nim'

ARG APP_VERSION
RUN cd /app/Nim && git checkout $APP_VERSION && ./build_all.sh

COPY app.nim /app

RUN /app/Nim/bin/nim compile -d:release /app/app.nim

CMD ["/app/app"]
