FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends bzip2

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/busybox && make allnoconfig && sed -e 's/# CONFIG_FEATURE_HTTPD_PROXY is not set/CONFIG_FEATURE_HTTPD_PROXY=y/' -e 's/# CONFIG_FEATURE_HTTPD_CGI/CONFIG_FEATURE_HTTPD_CGI=y/' -e 's/CONFIG_FEATURE_HTTPD_PORT_DEFAULT=0/CONFIG_FEATURE_HTTPD_PORT_DEFAULT=80/' -e 's/# CONFIG_HTTPD is not set/CONFIG_HTTPD=y/' -i .config && CFLAGS='-fsanitize=address,undefined' make -j"$(nproc)"

ARG CONFIG_FILE
COPY $CONFIG_FILE /etc/httpd.conf

ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /etc/httpd.conf

CMD ["/app/busybox/busybox", "httpd", "-f"]
