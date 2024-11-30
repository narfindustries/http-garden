FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby-dev ragel && gem install raindrops kgio olddoc rack sleepy_penguin kcar

ARG PARSER_REPO
RUN git clone --recurse-submodules "$PARSER_REPO"

ARG PARSER_VERSION
RUN cd /app/unicorn && git pull && git checkout "$PARSER_VERSION" && export LC_ALL=C.UTF-8 && make -j$(nproc) install-gem

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
COPY patch.diff .
RUN cd /app/yahns && git pull && git apply /app/patch.diff && git checkout "$APP_VERSION" && make install-gem

COPY yahns.conf .

ARG CONFIG_FILE
COPY $CONFIG_FILE ./config.ru
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" config.ru

CMD ["yahns", "-c", "yahns.conf"]
