FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install curl autoconf libtool patch python3-pip unzip virtualenv && curl -LO 'https://github.com/bazelbuild/bazelisk/releases/download/v1.25.0/bazelisk-amd64.deb' && dpkg -i bazelisk-amd64.deb && useradd --create-home user

USER user
WORKDIR /home/user
ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO" && bazel

ARG APP_VERSION
RUN cd envoy && git pull && git checkout "$APP_VERSION" && CC=clang bazel build envoy --define tcmalloc=gperftools --copt='-Wno-error' --cxxopt='-Wno-error' --config=asan

USER root
COPY config.yaml /app/config.yaml
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/config.yaml

CMD ["/home/user/envoy/bazel-bin/source/exe/envoy-static", "-c", "/app/config.yaml", "--concurrency", "1"]
