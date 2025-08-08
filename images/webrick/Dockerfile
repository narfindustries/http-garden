FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends ruby ruby-rack ruby-rackup

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/webrick \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && gem build \
 && gem install ./webrick*.gem

COPY config.ru .

CMD "rackup" "--quiet" "--host" "0.0.0.0" "--port" "80"
