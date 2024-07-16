FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/twisted && git pull && git checkout "$APP_VERSION" && pip install . --break-system-packages

COPY server.py .

CMD ["python3", "server.py"]
