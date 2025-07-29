FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends maven openjdk-21-jdk

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/undertow \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-$(dpkg --print-architecture)" \
 && mvn clean verify -Dmaven.test.failure.ignore=true

COPY GardenServer.java .
RUN javac -cp ./undertow/core/target/undertow-core-2.4.0.Beta1-SNAPSHOT.jar GardenServer.java

CMD java -cp .:./undertow/core/target/undertow-core-2.4.0.Beta1-SNAPSHOT.jar:./undertow/benchmarks/target/undertow-benchmarks.jar GardenServer
