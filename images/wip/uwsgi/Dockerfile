FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-dev libpcre2-dev && git clone "https://github.com/unbit/uwsgi"

ARG APP_VERSION
RUN cd /app/uwsgi && git checkout $APP_VERSION && make -j$(nproc) all

COPY ./server.py /app
CMD ["/app/uwsgi/uwsgi", "--http=0.0.0.0:80", "--http-keepalive", "--wsgi-file=server.py", "--wsgi-manage-chunked-input"]
