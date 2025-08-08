FROM http-garden-soil:latest

ARG BAZELISK_TAG
RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends curl autoconf libtool unzip lld-19 \
 && curl -LO "https://github.com/bazelbuild/bazelisk/releases/download/$BAZELISK_TAG/bazelisk-$(dpkg --print-architecture).deb" \
 && dpkg -i "bazelisk-$(dpkg --print-architecture).deb" \
 && useradd --create-home user

USER user
WORKDIR /home/user
ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# We use Envoy's own sanitizer config for this build because I couldn't get it working with mine.
ARG APP_VERSION
ARG APP_BRANCH
USER root
RUN su -c "cd /home/user/envoy \
        && unset CFLAGS CXXFLAGS LDFLAGS \
        && git pull origin ${APP_BRANCH} \
        && git checkout ${APP_VERSION} \
        && bazel build -c dbg --config=asan //source/exe:envoy-static --copt=-Wno-implicit-function-declaration --copt=-Wno-error --copt=-Wno-nullability-completeness --cxxopt=-Wno-implicit-function-declaration --cxxopt=-Wno-error --cxxopt=-Wno-nullability-completeness --host_copt=-Wno-implicit-function-declaration --host_copt=-Wno-error --host_copt=-Wno-nullability-completeness --host_cxxopt=-Wno-implicit-function-declaration --host_cxxopt=-Wno-error --host_cxxopt=-Wno-nullability-completeness --host_linkopt=-latomic --linkopt=-latomic --host_linkopt=-fuse-ld=lld --linkopt=-fuse-ld=lld --sandbox_debug --verbose_failures \
        && cp ./bazel-bin/source/exe/envoy-static /home/user" user \
 && rm -rf /home/user/.cache

ARG CONFIG_FILE
COPY $CONFIG_FILE /app/config.yaml
ARG BACKEND_HOST
ARG BACKEND_PORT
RUN sed -i -e "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" -e "s/BACKEND_PORT_PLACEHOLDER/$BACKEND_PORT/g" /app/config.yaml

CMD "/home/user/envoy-static" "-c" "/app/config.yaml" "--concurrency" "1"
