FROM http-garden-soil:latest

ARG BAZELISK_TAG
RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends curl autoconf libtool unzip \
 && curl -LO "https://github.com/bazelbuild/bazelisk/releases/download/$BAZELISK_TAG/bazelisk-$(dpkg --print-architecture).deb" \
 && dpkg -i "bazelisk-$(dpkg --print-architecture).deb" \
 && curl -LO "https://deb.debian.org/debian/pool/main/n/ncurses/libtinfo5_6.4-4_$(dpkg --print-architecture).deb" \
 && dpkg -i libtinfo5_*.deb \
 && useradd --create-home user

USER user
WORKDIR /home/user
ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# No sanitizers because this build system is so bad.
ARG APP_VERSION
ARG APP_BRANCH
USER root
RUN su -c "cd /home/user/envoy \
        && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
        && git pull origin ${APP_BRANCH} \
        && git checkout ${APP_VERSION} \
        && bazel build --config=clang -c dbg //source/exe:envoy-static --sandbox_debug --verbose_failures \
        && cp ./bazel-bin/source/exe/envoy-static /home/user" user \
 && rm -rf /home/user/.cache

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/config.yaml
ARG BACKEND_HOST=127.0.0.1
ARG BACKEND_PORT=56062
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /app/config.yaml

CMD python3 /tools/echo_server.py 127.0.0.1 "$((0xdafe))" & /home/user/envoy-static -c /app/config.yaml --concurrency 1
