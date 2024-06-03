FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install pkg-config libssl-dev zlib1g-dev libffi-dev && git clone "https://github.com/python/cpython" && git clone "https://github.com/pallets/werkzeug/"

RUN cd /app/cpython && git checkout $APP_VERSION && ./configure && make -j$(nproc) && make install

# We need to install this again because it was previously installed with the system python3.
RUN cd /app/python-afl && python3 -m pip install . --break-system-packages

ARG APP_VERSION
RUN cd /app/werkzeug && git checkout $APP_VERSION && python3 -m pip install . --break-system-packages

COPY ./server.py /app

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "python3", "./server.py"]
