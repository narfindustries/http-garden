FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip python3-gevent && git clone "https://github.com/benoitc/gunicorn"

ARG APP_VERSION
RUN cd /app/gunicorn && git checkout $APP_VERSION && pip3 install . --break-system-packages

COPY ./server.py /app
COPY ./gunicorn.conf.py /gunicorn.conf.py

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "python3", "-m", "gunicorn", "--permit-unconventional-http-method", "--worker-class=gevent", "--config=/gunicorn.conf.py", "--workers=1", "--worker-connections=1000", "--bind", "0.0.0.0:80", "server:app"]
