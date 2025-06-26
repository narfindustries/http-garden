FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends autoconf automake libtool make tar libaio-dev libssl-dev libapr1-dev lksctp-tools openjdk-21-jdk gcc cmake ninja-build cargo

ARG APP_REPO
ARG APP_BRANCH
RUN git clone --branch "$APP_BRANCH" --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/netty \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && unset CC CXX CXXFLAGS CFLAGS LDFLAGS \
 && export CC=gcc-14 CXX=g++-14 \
 && export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
 && ./mvnw clean install -DskipTests -T1C

COPY GardenServer.java /app

RUN export VERSION="$(ls /app/netty/all/target/netty-all-*.Final-SNAPSHOT.jar | grep -oP '\d\.\d\.\d\d\d')" \
 && javac -cp /app/netty/transport/target/netty-transport-$VERSION.Final-SNAPSHOT.jar:/app/netty/common/target/netty-common-$VERSION.Final-SNAPSHOT.jar:/app/netty/handler/target/netty-handler-$VERSION.Final-SNAPSHOT.jar:/app/netty/buffer/target/netty-buffer-$VERSION.Final-SNAPSHOT.jar:/app/netty/codec-http/target/netty-codec-http-$VERSION.Final-SNAPSHOT.jar:/app/netty/codec/target/netty-codec-$VERSION.Final-SNAPSHOT.jar GardenServer.java

CMD export VERSION="$(ls /app/netty/all/target/netty-all-*.Final-SNAPSHOT.jar | grep -oP '\d\.\d\.\d\d\d')" \
 && exec java -cp /app/netty/transport/target/netty-transport-$VERSION.Final-SNAPSHOT.jar:/app/netty/common/target/netty-common-$VERSION.Final-SNAPSHOT.jar:/app/netty/handler/target/netty-handler-$VERSION.Final-SNAPSHOT.jar:/app/netty/buffer/target/netty-buffer-$VERSION.Final-SNAPSHOT.jar:/app/netty/codec-http/target/netty-codec-http-$VERSION.Final-SNAPSHOT.jar:/app/netty/codec/target/netty-codec-$VERSION.Final-SNAPSHOT.jar:. GardenServer
