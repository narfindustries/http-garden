FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3

COPY server.py .

CMD ["python3", "./server.py"]
