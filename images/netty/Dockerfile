FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install autoconf automake libtool make tar libaio-dev libssl-dev libapr1-dev lksctp-tools openjdk-23-jdk gcc && git clone 'https://github.com/netty/netty'

ARG APP_VERSION
RUN cd /app/netty && git checkout "$APP_VERSION" && export JAVA_HOME=/usr/lib/jvm/java-23-openjdk-amd64 && ./mvnw clean install -DskipTests -T1C

COPY GardenServer.java /app

# Wildcard expansion within the CLASSPATH doesn't work, so the version is hardcoded for now.
RUN javac -cp /app/netty/transport/target/netty-transport-4.1.112.Final-SNAPSHOT.jar:/app/netty/common/target/netty-common-4.1.112.Final-SNAPSHOT.jar:/app/netty/handler/target/netty-handler-4.1.112.Final-SNAPSHOT.jar:/app/netty/buffer/target/netty-buffer-4.1.112.Final-SNAPSHOT.jar:/app/netty/codec-http/target/netty-codec-http-4.1.112.Final-SNAPSHOT.jar:/app/netty/codec/target/netty-codec-4.1.112.Final-SNAPSHOT.jar GardenServer.java

CMD java -cp /app/netty/transport/target/netty-transport-4.1.112.Final-SNAPSHOT.jar:/app/netty/common/target/netty-common-4.1.112.Final-SNAPSHOT.jar:/app/netty/handler/target/netty-handler-4.1.112.Final-SNAPSHOT.jar:/app/netty/buffer/target/netty-buffer-4.1.112.Final-SNAPSHOT.jar:/app/netty/codec-http/target/netty-codec-http-4.1.112.Final-SNAPSHOT.jar:/app/netty/codec/target/netty-codec-4.1.112.Final-SNAPSHOT.jar:. GardenServer
