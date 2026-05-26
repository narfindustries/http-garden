FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends openjdk-21-jdk wget maven

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd grizzly \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && mvn clean install -Dmaven.test.skip=true

COPY GardenServer.java .

# For some reason, this works
RUN javac -cp ./grizzly/modules/bundles/http-all/target/grizzly-http-all-*-SNAPSHOT.jar GardenServer.java

# But here, we need a VERSION variable. A dumb inconsistency between java and javac.
CMD export VERSION="$(ls /app/grizzly/modules/bundles/http-all/target/grizzly-http-all-*-SNAPSHOT.jar | grep -oP '\d+(\.\d+)*')" && java -cp ".:/app/grizzly/modules/bundles/http-all/target/grizzly-http-all-$VERSION-SNAPSHOT.jar" GardenServer
