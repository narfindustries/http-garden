FROM http-garden-python-soil:latest

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/uvicorn \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && pip install --no-cache-dir . \
 && sed -i "s/if __name__ == '__main__':/if __name__ == '__main__':\n    import afl\n    afl.init();/" "$(which uvicorn)"

COPY ./server.py /app
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "uvicorn", "--no-access-log", "--host", "0.0.0.0", "--port", "80", "server:app"]
