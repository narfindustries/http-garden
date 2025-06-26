FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends openjdk-21-jdk wget maven

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# Build Jetty
WORKDIR /app/jetty.project
ARG APP_VERSION
ARG APP_BRANCH
RUN git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && mvn -Pfast clean install

# Build our servlet
COPY ./Server.java .
RUN javac -cp ./jetty-home/target/jetty-home/lib/jetty-jakarta-servlet-api-*.jar Server.java

# Configure Jetty
WORKDIR /app/jetty.project/base
RUN java -jar ../jetty-home/target/jetty-home/start.jar --add-module=http,ee10-deploy
RUN mkdir -p webapps/root/WEB-INF/classes \
 && cp ../Server.class webapps/root/WEB-INF/classes
COPY web.xml webapps/root/WEB-INF

CMD ["java", "-jar", "../jetty-home/target/jetty-home/start.jar", "jetty.http.port=80"]
