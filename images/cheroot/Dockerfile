FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip && git clone 'https://github.com/cherrypy/cheroot'

ARG APP_VERSION
RUN cd /app/cheroot && git checkout $APP_VERSION && pip3 install --break-system-packages .

COPY server.py .

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "python3", "server.py"]
