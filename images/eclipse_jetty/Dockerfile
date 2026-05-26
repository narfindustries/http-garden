FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends openjdk-21-jdk wget

ARG APP_REPO
ARG APP_BRANCH
RUN git clone -b "$APP_BRANCH" --recurse-submodules "$APP_REPO"

# Get Maven 4 (undocumented requirement)
RUN wget https://dlcdn.apache.org/maven/maven-4/4.0.0-rc-5/binaries/apache-maven-4.0.0-rc-5-bin.tar.gz \
 && tar xf apache-maven-*-bin.tar.gz \
 && rm apache-maven-*-bin.tar.gz

# Build Jetty
WORKDIR /app/jetty.project
ARG APP_VERSION
RUN git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ../apache-maven-4.0.0-rc-5/bin/mvn -Pfast clean install -e   -Djakarta-persistence-api.version=3.1.0   -Djakarta.messaging-api.version=3.1.0 -pl '!jetty-p2' -am

# Build our servlet
COPY ./Server.java .
RUN javac -cp ./jetty-home/target/jetty-home/lib/jetty-jakarta-servlet-api-*.jar Server.java

# Configure Jetty
WORKDIR /app/jetty.project/base
RUN java -jar ../jetty-home/target/jetty-home/start.jar --add-module=http,http2c,ee10-deploy
RUN mkdir -p webapps/root/WEB-INF/classes \
 && cp ../Server.class webapps/root/WEB-INF/classes
COPY web.xml webapps/root/WEB-INF

CMD "java" "-jar" "../jetty-home/target/jetty-home/start.jar" "jetty.http.port=80"
