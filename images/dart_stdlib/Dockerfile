FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends xz-utils curl

RUN git clone --depth 1 --recurse-submodules https://chromium.googlesource.com/chromium/tools/depot_tools.git && /app/depot_tools/fetch dart

ARG APP_VERSION
RUN export PATH="$PATH:$PWD/depot_tools" && cd sdk && git checkout "$APP_VERSION" && /app/depot_tools/gclient sync && ./tools/build.py --mode release --arch x64 create_sdk

COPY server.dart .
CMD ["./sdk/sdk/bin/dart", "server.dart"]
