FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby ruby-rack

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/webrick && git pull && git checkout "$APP_VERSION" && gem build && gem install ./webrick*.gem

COPY config.ru .

CMD ["rackup", "--host", "0.0.0.0", "--port", "80"]
