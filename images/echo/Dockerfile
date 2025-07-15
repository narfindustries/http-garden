FROM http-garden-soil:latest

ARG APP_REPO
ARG APP_BRANCH
ARG APP_VERSION
RUN git clone "$APP_REPO" \
 && cd http-garden \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION"

COPY echo_server.py /app/http-garden/tools
CMD ["python3", "./http-garden/tools/echo_server.py", "0.0.0.0", "80"]
