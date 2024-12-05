FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends pkg-config autoconf-archive automake libssl-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/cpython && git pull && git checkout "$APP_VERSION" && ./configure --enable-optimizations && make -j"$(nproc)"

RUN /app/cpython/python -m venv /app/venv && . /app/venv/bin/activate && pip install /app/python-afl

COPY ./server.py /app
CMD ["/app/venv/bin/python", "/app/server.py"]
