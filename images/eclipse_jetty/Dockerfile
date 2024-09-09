FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends openjdk-17-jdk wget

# We also need Maven >=3.9.0, but that's not packaged for Trixie, so we have to get it from the source.
RUN wget 'https://dlcdn.apache.org/maven/maven-3/3.9.8/binaries/apache-maven-3.9.8-bin.tar.gz' -O maven.tgz && tar xf 'maven.tgz'

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# Build Jetty
WORKDIR /app/jetty.project
ARG APP_VERSION
RUN git pull && git checkout "$APP_VERSION" && /app/apache-maven-*/bin/mvn -Pfast clean install

# Build our servlet
COPY ./Server.java .
RUN javac -cp ./jetty-home/target/jetty-home/lib/jetty-jakarta-servlet-api-*.jar Server.java

# Configure Jetty
WORKDIR /app/jetty.project/base
RUN java -jar ../jetty-home/target/jetty-home/start.jar --add-module=http,ee10-deploy
RUN mkdir -p webapps/root/WEB-INF/classes && cp ../Server.class webapps/root/WEB-INF/classes
COPY web.xml webapps/root/WEB-INF

CMD ["java", "-jar", "../jetty-home/target/jetty-home/start.jar", "jetty.http.port=80"]
