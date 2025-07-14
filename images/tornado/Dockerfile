FROM http-garden-soil:latest

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/tornado \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && pip install --no-cache-dir .

COPY ./server.py /app
CMD ["python3", "./server.py"]
