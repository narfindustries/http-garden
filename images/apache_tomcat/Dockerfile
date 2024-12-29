FROM http-garden-soil:latest

WORKDIR /app
RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends openjdk-21-jdk ant git

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

WORKDIR /app/tomcat
ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/tomcat \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && cp build.properties.default build.properties \
 && sed -i 's/8080/80/g' conf/server.xml
RUN ant \
 && cp -r ./output/build/* .

COPY ./Server.java .
RUN javac -cp ./output/build/lib/servlet-api.jar Server.java \
 && mv Server.class lib

COPY web.xml ./webapps/ROOT/WEB-INF

CMD ["/app/tomcat/bin/catalina.sh", "run"]
