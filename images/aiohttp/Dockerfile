FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install libffi-dev python3-venv && python3 -m venv /app/venv

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# ENV YARL_NO_EXTENSIONS=1
ENV AIOHTTP_NO_EXTENSIONS=1
ARG APP_VERSION
RUN cd /app/aiohttp && git pull && git checkout "$APP_VERSION" && git submodule update --init --recursive && . /app/venv/bin/activate && pip install . && pip install /app/python-afl

COPY ./server.py /app
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "/app/aiohttp/env/bin/python3", "./server.py"]
