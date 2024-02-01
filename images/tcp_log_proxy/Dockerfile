FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3

COPY server.py .

ARG BACKEND
ENV BACKEND=$BACKEND
CMD exec python3 ./server.py --backend $BACKEND --backend-port 80 --frontend-port 80
