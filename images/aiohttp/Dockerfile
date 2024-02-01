FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install libffi-dev python3-venv && git clone "https://github.com/aio-libs/aiohttp" && python3 -m venv /app/aiohttp/env

ENV AIOHTTP_NO_EXTENSIONS=1
ARG APP_VERSION
RUN cd /app/aiohttp && git checkout $APP_VERSION && git submodule update --init --recursive && . /app/aiohttp/env/bin/activate && pip install . && pip install /app/python-afl

COPY ./server.py /app
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "/app/aiohttp/env/bin/python3", "./server.py"]
