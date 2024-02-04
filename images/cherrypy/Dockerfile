FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip && git clone 'https://github.com/cherrypy/cherrypy' && git clone 'https://github.com/cherrypy/cheroot'

ARG APP_VERSION
ARG PARSER_VERSION
RUN cd /app/cheroot && git checkout $CHEROOT_VERSION && pip3 install --break-system-packages .
RUN cd /app/cherrypy && git checkout $APP_VERSION && pip3 install --break-system-packages .

COPY server.py .

# For some reason, afl-showmap just isn't working...
CMD ["python3", "server.py"]
