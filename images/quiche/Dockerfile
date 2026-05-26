FROM http-garden-soil:latest

ARG BAZELISK_TAG
RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends curl libicu-dev libabsl-dev \
 && curl -LO "https://github.com/bazelbuild/bazelisk/releases/download/$BAZELISK_TAG/bazelisk-$(dpkg --print-architecture).deb" \
 && dpkg -i "bazelisk-$(dpkg --print-architecture).deb" \
 && useradd --create-home user

USER user
WORKDIR /home/user
ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_BRANCH
ARG APP_VERSION
RUN cd quiche \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && bazel build ...

USER root
WORKDIR /app

COPY garden.cpp .

# RUN "$CXX" $CXXFLAGS -I/home/user/quiche/ -I/home/user/quiche/quiche/common/platform/default /home/user/quiche/bazel-bin/quiche/libbalsa.a garden.cpp -o garden

CMD ["./garden"]
