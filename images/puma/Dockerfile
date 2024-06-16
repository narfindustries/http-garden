FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby-dev && gem install sinatra && git clone "https://github.com/puma/puma"

ARG APP_VERSION
RUN cd /app/puma && git pull && git checkout "$APP_VERSION" && gem build && gem install ./puma*.gem

COPY ./config.ru .
COPY ./puma_config.rb .

CMD ["puma", "--port", "80", "-C", "puma_config.rb"]
