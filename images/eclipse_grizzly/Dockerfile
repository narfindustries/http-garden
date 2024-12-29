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
RUN javac -cp ./grizzly/modules/bundles/http-all/target/grizzly-http-all-4.0.0-SNAPSHOT.jar GardenServer.java

CMD java -cp .:./grizzly/modules/bundles/http-all/target/grizzly-http-all-4.0.0-SNAPSHOT.jar GardenServer
