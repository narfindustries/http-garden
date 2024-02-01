FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip && git clone "https://github.com/tornadoweb/tornado"

ARG APP_VERSION
RUN cd /app/tornado && git checkout $APP_VERSION && pip3 install --break-system-packages .

COPY ./server.py /app
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "python3", "./server.py"]
