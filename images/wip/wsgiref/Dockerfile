FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install pkg-config libssl-dev zlib1g-dev libffi-dev && git clone "https://github.com/python/cpython"

ARG APP_VERSION
RUN cd cpython && git checkout $APP_VERSION && ./configure && make -j$(nproc) && make install

COPY server.py .

CMD ["python3", "server.py"]
