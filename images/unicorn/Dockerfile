FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install ruby-dev ragel && gem install raindrops kgio olddoc rack && git clone "https://yhbt.net/unicorn.git/"

ARG APP_VERSION
RUN cd /app/unicorn && git checkout $APP_VERSION && export LC_ALL=C.UTF-8 && make -j$(nproc) install-gem

COPY config.ru .

CMD ["unicorn", "--port", "80"]
