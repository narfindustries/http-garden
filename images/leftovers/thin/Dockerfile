FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby-dev libssl-dev && gem install sinatra && git clone "https://github.com/macournoyer/thin"

ARG APP_VERSION
RUN cd /app/thin && git checkout "$APP_VERSION" && gem build && gem install ./thin*.gem

COPY ./server.rb .

CMD ["ruby", "server.rb"]
