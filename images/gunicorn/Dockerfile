FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip python3-gevent && git clone "https://github.com/benoitc/gunicorn"

ARG APP_VERSION
RUN cd /app/gunicorn && git checkout $APP_VERSION && pip3 install . --break-system-packages

COPY ./server.py /app
# For some reason, afl-showmap just isn't working...
CMD ["python3", "-m", "gunicorn", "--worker-class=gevent", "--workers=1", "--worker-connections=1000", "--bind", "0.0.0.0:80", "server:app"]
