FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby && git clone https://github.com/ruby/webrick

ARG APP_VERSION
RUN cd /app/webrick && git checkout $APP_VERSION && gem build && gem install ./webrick*.gem

COPY server.rb .

CMD ["ruby", "server.rb"]
