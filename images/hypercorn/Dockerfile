FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip && git clone 'https://github.com/pgjones/hypercorn'

ARG APP_VERSION
RUN cd /app/hypercorn && git checkout $APP_VERSION && pip install . --break-system-packages

COPY server.py .

CMD ["hypercorn", "server:app", "-b", "0.0.0.0:80"]
