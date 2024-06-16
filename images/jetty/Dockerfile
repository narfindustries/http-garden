FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install maven openjdk-17-jdk && git clone https://github.com/eclipse/jetty.project

# Build Jetty
WORKDIR /app/jetty.project
ARG APP_VERSION
RUN git pull && git checkout "$APP_VERSION" && mvn -Pfast clean install

# Build our servlet
COPY ./Server.java .
RUN javac -cp ./jetty-home/target/jetty-home/lib/jetty-jakarta-servlet-api-*.jar Server.java

# Configure Jetty
WORKDIR /app/jetty.project/base
RUN java -jar ../jetty-home/target/jetty-home/start.jar --add-module=http,ee10-deploy
RUN mkdir -p webapps/root/WEB-INF/classes && cp ../Server.class webapps/root/WEB-INF/classes
COPY web.xml webapps/root/WEB-INF

CMD ["java", "-jar", "../jetty-home/target/jetty-home/start.jar", "jetty.http.port=80"]
