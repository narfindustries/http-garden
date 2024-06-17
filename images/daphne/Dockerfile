FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/daphne && git pull && git checkout "$APP_VERSION" && pip3 install --break-system-packages "Twisted[tls,http2]" && pip3 install --break-system-packages .

RUN sed -i "s/if __name__ == '__main__':/if __name__ == '__main__':\n    import afl\n    afl.init();/" $(which daphne)

COPY ./server.py /app
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "daphne", "-b", "0.0.0.0", "-p", "80", "server:app"]
