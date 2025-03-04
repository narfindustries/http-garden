FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends clang-17 lld-17 curl autoconf libtool patch python3-pip unzip virtualenv \
 && curl -LO 'https://github.com/bazelbuild/bazelisk/releases/download/v1.25.0/bazelisk-amd64.deb' \
 && dpkg -i bazelisk-amd64.deb \
 && useradd --create-home user

USER user
WORKDIR /home/user
ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO" && bazel

ARG APP_VERSION
ARG APP_BRANCH
USER root
RUN su -c 'cd envoy \
        && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
        && git pull origin "$APP_BRANCH" \
        && git checkout "$APP_VERSION" \
        && CC=clang-17 LD=lld-17 bazel build -c opt envoy --define tcmalloc=gperftools --copt="-Wno-error" --cxxopt="-Wno-error" \
        && cp ./bazel-bin/source/exe/envoy-static /home/user' user \
 && rm -rf /home/user/.cache

COPY config.yaml /app/config.yaml
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/config.yaml

CMD ["/home/user/envoy-static", "-c", "/app/config.yaml", "--concurrency", "1"]
