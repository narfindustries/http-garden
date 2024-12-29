FROM http-garden-python-soil:latest

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/hypercorn \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && pip install --no-cache-dir . \
 && sed -i "s/^from hypercorn.__main__ import main/import afl\nafl.init()\nfrom hypercorn.__main__ import main/" "$(which hypercorn)"

COPY server.py .

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "hypercorn", "server:app", "-b", "0.0.0.0:80"]
