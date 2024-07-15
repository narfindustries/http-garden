FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends ruby-dev && gem install sinatra

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/puma && git pull && git checkout "$APP_VERSION" && gem build && gem install ./puma*.gem

COPY ./config.ru .
COPY ./puma_config.rb .

CMD ["puma", "--port", "80", "-C", "puma_config.rb"]
