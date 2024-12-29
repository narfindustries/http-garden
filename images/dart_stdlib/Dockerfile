FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends xz-utils curl

ARG APP_VERSION
ARG APP_BRANCH
RUN git clone --depth 1 --recurse-submodules https://chromium.googlesource.com/chromium/tools/depot_tools.git \
 && /app/depot_tools/fetch dart \
 && export PATH="$PATH:$PWD/depot_tools" \
 && cd sdk \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && /app/depot_tools/gclient sync -D \
 && ./tools/build.py --mode release --arch x64 create_sdk \
 && mv /app/sdk/sdk /app/sdk/out /tmp \
 && rm -rf /app/sdk \
 && mkdir /app/sdk \
 && mv /tmp/sdk /tmp/out /app/sdk

COPY server.dart .
CMD ["./sdk/sdk/bin/dart", "server.dart"]
