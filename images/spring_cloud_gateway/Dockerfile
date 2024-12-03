FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends openjdk-17-jdk

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd spring-cloud-gateway && git pull && git checkout "$APP_VERSION"

COPY application.yml /app/spring-cloud-gateway/spring-cloud-gateway-sample/src/main/resources/application.yml
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /app/spring-cloud-gateway/spring-cloud-gateway-sample/src/main/resources/application.yml

RUN cd spring-cloud-gateway && export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 && ./mvnw clean install -Dmaven.test.skip=true -Dmaven.javadoc.skip=true

RUN cp /app/spring-cloud-gateway/spring-cloud-gateway-sample/target/spring-cloud-gateway-sample-*-SNAPSHOT.jar /app/spring-cloud-gateway/spring-cloud-gateway-sample/target/spring-cloud-gateway-sample.jar

CMD ["java", "-jar", "/app/spring-cloud-gateway/spring-cloud-gateway-sample/target/spring-cloud-gateway-sample.jar"]
