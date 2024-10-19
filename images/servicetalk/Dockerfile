FROM http-garden-soil:latest

# Note: we use Java 22 because ServiceTalk uses Gradle 8.8, and 22 is the most recent Java version that it supports
RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends openjdk-22-jdk libslf4j-java

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd /app/servicetalk && git pull && git checkout "$APP_VERSION" && ./gradlew build -x test

COPY GardenServer.java /app

RUN javac -cp $(find . -name '*SNAPSHOT.jar' | python3 -c 'import sys; print(":".join(sys.stdin.read().split()))') GardenServer.java

CMD java -cp \
"\
:/usr/share/java/slf4j-simple.jar\
:$(find /app/servicetalk -name '*SNAPSHOT.jar' | python3 -c 'import sys; print(":".join(sys.stdin.read().split()))')\
:$(find /root/.gradle/caches/modules-*/files-*/org.slf4j/slf4j-api -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-transport -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-common -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-codec-http2 -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-codec -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-transport-classes-epoll -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-buffer -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-handler -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-transport-native-unix-common -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-transport-native-epoll -name '*x86*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/org.jctools/jctools-core -name '*.jar' | head -n 1)\
:$(find /root/.gradle/caches/modules-*/files-*/io.netty/netty-codec-http -name '*.jar' | head -n 1)\
:.\
" GardenServer
