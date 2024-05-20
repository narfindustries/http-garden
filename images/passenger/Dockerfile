FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-flask ruby-dev libcurl4-openssl-dev libssl-dev zlib1g-dev rake libpcre2-dev wget coreutils procps && git clone --recurse-submodules "https://github.com/phusion/passenger"

ARG APP_VERSION
RUN cd passenger && git checkout $APP_VERSION && gem build && gem install ./passenger*.gem && passenger-config compile-agent --auto && passenger-config install-standalone-runtime --auto && passenger-config build-native-support

COPY passenger_wsgi.py .

RUN ln -s $(which python3) /usr/bin/python

CMD ["passenger", "start", "--engine", "builtin", "--port", "80"]
