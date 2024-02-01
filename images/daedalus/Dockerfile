FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install cabal-install python3

RUN git clone https://github.com/GaloisInc/daedalus.git
WORKDIR /app/daedalus/
RUN cabal update
RUN cabal install exe:daedalus --installdir=/bin --overwrite-policy=always

WORKDIR /app/daedalus/formats/http

COPY ./server.py .
CMD ["python3", "server.py"]
