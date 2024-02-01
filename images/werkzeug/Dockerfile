FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install pkg-config libssl-dev zlib1g-dev libffi-dev && git clone "https://github.com/python/cpython" && git clone "https://github.com/pallets/werkzeug/"

RUN cd /app/cpython && git checkout $APP_VERSION && ./configure && make -j$(nproc) && make install

ARG APP_VERSION
RUN cd /app/werkzeug && git checkout $APP_VERSION && python3 -m pip install . --break-system-packages

COPY ./server.py /app

CMD ["python3", "./server.py"]
