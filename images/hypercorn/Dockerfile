FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install python3-pip && git clone 'https://github.com/pgjones/hypercorn'

ARG APP_VERSION
RUN cd /app/hypercorn && git checkout $APP_VERSION && pip install . --break-system-packages

# observation: /tmp/hypercorn/trace empty if initialized later
RUN sed -i "s/^from hypercorn.__main__ import main/import afl\nafl.init()\nfrom hypercorn.__main__ import main/" $(which hypercorn)

COPY server.py .

CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "hypercorn", "server:app", "-b", "0.0.0.0:80"]
