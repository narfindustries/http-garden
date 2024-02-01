FROM debian:bullseye-slim
# Note to self: never try to port this to Alpine again. You have tried and failed twice. It's not worth it.
# Also don't try building from source. Their build scripts are all kinds of broken. Their repo has the latest release anyway.
# Consider using the unstable channel: https://openlitespeed.org/kb/upgrade-ols-to-edge-tier/#Setup-2

WORKDIR /app

RUN apt -y update && apt -y upgrade && apt -y install wget curl && wget -O - https://repo.litespeed.sh | bash && apt -y update && apt -y install openlitespeed lsphp81 lsphp81-common lsphp81-curl lsphp81-mysql lsphp81-opcache lsphp81-imap lsphp81-opcache procps

RUN rm -rf /usr/local/lsws/Example && mkdir -p /usr/local/lsws/Example/html
ARG CONFIG_FILE
COPY $CONFIG_FILE /usr/local/lsws/conf/httpd_config.conf
ARG VHCONF
COPY $VHCONF /usr/local/lsws/conf/vhosts/Example/vhconf.conf
COPY index.php /usr/local/lsws/Example/html/

CMD ["/usr/local/lsws/bin/openlitespeed", "-d"]
