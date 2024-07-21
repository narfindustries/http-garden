FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends openjdk-17-jdk wget

# We also need Maven >=3.9.0, but that's not packaged for Trixie, so we have to get it from the source.
RUN wget 'https://dlcdn.apache.org/maven/maven-3/3.9.8/binaries/apache-maven-3.9.8-bin.tar.gz' -O maven.tgz && tar xf 'maven.tgz'

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# Build Jetty
ARG APP_VERSION
RUN cd /app/jetty.project && git pull && git checkout "$APP_VERSION" && /app/apache-maven-*/bin/mvn -Pfast install -DskipTests

# Build our servlet
COPY ./Server.java /app
RUN javac -cp /app/jetty.project/jetty-home/target/jetty-home/lib/jetty-jakarta-servlet-api-*.jar Server.java

# Configure Jetty
RUN java -jar /app/jetty.project/jetty-home/target/jetty-home/start.jar --add-module=http,ee10-deploy
RUN mkdir -p /app/jetty.project/base/webapps/root/WEB-INF/classes && cp /app/Server.class /app/jetty.project/base/webapps/root/WEB-INF/classes
COPY web.xml /app/jetty.project/base/webapps/root/WEB-INF

CMD ["java", "-jar", "/app/jetty.project/jetty-home/target/jetty-home/start.jar", "jetty.http.port=80"]
