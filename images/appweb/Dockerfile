FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install libssl-dev libapr1-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

RUN arch="$(uname -m)"; ([ "$arch" = "x86_64" ] && echo "x64" || echo "$arch") > /app/arch.txt

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/appweb \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && git submodule update --init --recursive \
 && make \
 && make install

COPY server.c .
RUN "$CC" $CFLAGS -I/app/appweb/build/linux-$(cat /app/arch.txt)-default/inc server.c -shared -o libmod_echo.so -L/app/appweb/build/linux-$(cat /app/arch.txt)-default/bin -lappweb -lmpr -lhttp -lapr-1

ARG CONFIG_FILE
COPY $CONFIG_FILE ./appweb.conf
ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" appweb.conf

CMD export LD_LIBRARY_PATH="/app/appweb/build/linux-$(cat /app/arch.txt)-default/bin" \
 && exec "/app/appweb/build/linux-$(cat /app/arch.txt)-default/bin/appweb"
