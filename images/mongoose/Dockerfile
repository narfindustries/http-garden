FROM http-garden-soil:latest

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/mongoose \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION"

ARG SERVER_SOURCE
COPY $SERVER_SOURCE /app/mongoose/tutorials/http/echo/main.c

RUN cd /app/mongoose/tutorials/http/echo \
 && "$CC" $CFLAGS -I/app/mongoose main.c /app/mongoose/mongoose.c -o echo

CMD ["/app/mongoose/tutorials/http/echo/echo"]
