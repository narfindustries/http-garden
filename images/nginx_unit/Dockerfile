FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install libpcre2-dev curl libssl-dev mercurial && hg clone "https://hg.nginx.org/unit" && hg clone "http://hg.nginx.org/njs"

RUN cd /app/njs && ./configure --cc='afl-cc' --cc-opt='-fsanitize=address,undefined' --ld-opt='-fsanitize=address,undefined' && make -j$(nproc)

ARG APP_VERSION
RUN cd /app/unit && hg update $APP_VERSION && ./configure --cc='afl-cc' --cc-opt='-I../njs/src/ -I../njs/build/' --ld-opt='-L../njs/build/' && ./configure python --config=python3-config && make -j$(nproc) && make install libunit-install

COPY wsgi.py /www/

COPY start.sh .
CMD exec unitd --no-daemon
