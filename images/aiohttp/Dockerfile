FROM http-garden-python-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends libffi-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ENV AIOHTTP_NO_EXTENSIONS=1
ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/aiohttp \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && git submodule update --init --recursive \
 && pip install --no-cache-dir .

COPY ./server.py /app
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "/app/venv/bin/python3", "./server.py"]
