FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends python3

COPY server.py .

CMD ["python3", "./server.py"]
