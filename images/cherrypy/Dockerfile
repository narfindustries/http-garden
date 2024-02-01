FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip && git clone 'https://github.com/cherrypy/cherrypy'

ARG APP_VERSION
RUN cd /app/cherrypy && git checkout $APP_VERSION && pip3 install --break-system-packages .

COPY server.py .

# For some reason, afl-showmap just isn't working...
CMD ["python3", "server.py"]
