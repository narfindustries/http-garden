FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && pip install gevent

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/gunicorn \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && pip install --no-cache-dir .

COPY ./server.py /app

CMD ["python3", "-m", "gunicorn", "--worker-class=gevent", "--workers=1", "--worker-connections=1000", "--bind", "0.0.0.0:80", "server:app"]
