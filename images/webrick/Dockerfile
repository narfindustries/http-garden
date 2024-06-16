FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby ruby-rack && git clone https://github.com/ruby/webrick

ARG APP_VERSION
RUN cd /app/webrick && git pull && git checkout "$APP_VERSION" && gem build && gem install ./webrick*.gem

COPY config.ru .

CMD ["rackup", "--host", "0.0.0.0", "--port", "80"]
