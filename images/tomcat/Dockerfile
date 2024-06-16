FROM ubuntu:24.04
# For now, there is no Debian release that packages openjdk 21, so we need to use Ubuntu

WORKDIR /app
RUN apt -y update && apt -y upgrade && apt -y install openjdk-21-jdk ant git && git clone https://github.com/apache/tomcat

WORKDIR /app/tomcat
ARG APP_VERSION
RUN git pull && git checkout "$APP_VERSION" && cp build.properties.default build.properties && sed -i 's/8080/80/g' conf/server.xml
RUN ant && cp -r ./output/build/* .

COPY ./Server.java .
RUN javac -cp ./output/build/lib/servlet-api.jar Server.java && mv Server.class lib

COPY web.xml ./webapps/ROOT/WEB-INF

CMD ["/app/tomcat/bin/catalina.sh", "run"]
