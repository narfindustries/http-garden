FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby-dev && gem install sinatra && git clone "https://github.com/puma/puma"

ARG APP_VERSION
RUN cd /app/puma && git checkout $APP_VERSION && gem build && gem install ./puma*.gem

COPY ./config.ru .

CMD ["puma", "--port", "80"]
