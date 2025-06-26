FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install zip && git clone 'https://github.com/RealTimeLogic/BAS' && git clone 'https://github.com/RealTimeLogic/BAS-Resources'

RUN chmod +x ./BAS/LinuxBuild.sh && ./BAS/LinuxBuild.sh

COPY mako.conf /app
RUN mkdir /app/www
COPY index.lsp /app/www

CMD ["./mako"]
