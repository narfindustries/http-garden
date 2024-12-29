FROM http-garden-python-soil:latest

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/waitress \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && pip install --no-cache-dir .

COPY server.py .
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "python3", "server.py"]
