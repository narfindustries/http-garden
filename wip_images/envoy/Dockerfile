FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install wget python3
RUN wget "https://github.com/bazelbuild/bazelisk/releases/download/v1.17.0/bazelisk-linux-amd64" -O /bin/bazel && chmod +x /bin/bazel

RUN useradd --create-home user
ARG APP_VERSION
RUN su - user -c "git clone https://github.com/envoyproxy/envoy && cd envoy && git checkout $APP_VERSION && bazel build --config=clang-asan --verbose_failures -c opt envoy"

USER root
RUN cp /home/user/envoy/bazel-out/k8-opt/bin/source/exe/envoy-static /bin/envoy
COPY envoy.yaml .
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/envoy.yaml

CMD ["envoy", "-c", "envoy.yaml"]
