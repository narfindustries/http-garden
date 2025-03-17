FROM http-garden-python-soil:latest

# Unsetting because we don't need a sanitized/AFL build of gevent
RUN unset CC CXX CFLAGS CXXFLAGS LDFLAGS && pip install gevent

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/gunicorn \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && pip install --no-cache-dir .

COPY ./server.py /app
COPY ./gunicorn.conf.py /app/gunicorn.conf.py

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "python3", "-m", "gunicorn", "--worker-class=gevent", "--config=/app/gunicorn.conf.py", "--workers=1", "--worker-connections=1000", "--bind", "0.0.0.0:80", "server:app"]
