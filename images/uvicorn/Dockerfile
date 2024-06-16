FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip && git clone "https://github.com/encode/uvicorn"

ARG APP_VERSION
RUN cd /app/uvicorn && git pull && git checkout "$APP_VERSION" && pip3 install . --break-system-packages

RUN sed -i "s/if __name__ == '__main__':/if __name__ == '__main__':\n    import afl\n    afl.init();/" $(which uvicorn)

COPY ./server.py /app
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "uvicorn", "--host", "0.0.0.0", "--port", "80", "server:app"]
