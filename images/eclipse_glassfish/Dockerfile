FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends openjdk-21-jdk wget

# We also need Maven >=3.9.0, but that's not packaged for Trixie, so we have to get it from the source.
RUN wget 'https://dlcdn.apache.org/maven/maven-3/3.9.8/binaries/apache-maven-3.9.8-bin.tar.gz' -O maven.tgz && tar xf 'maven.tgz'

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd glassfish && git pull && git checkout "$APP_VERSION" && /app/apache-maven-*/bin/mvn clean install -Dmaven.test.skip=true -Pfastest

COPY Server.java .
RUN javac -cp /app/glassfish/appserver/distributions/glassfish/target/dependency/jakarta.servlet-api.jar Server.java

COPY web.xml /app/garden_webapp/WEB-INF/web.xml
RUN mkdir -p /app/garden_webapp/WEB-INF/classes && mv Server.class /app/garden_webapp/WEB-INF/classes

RUN java -jar /app/glassfish/appserver/distributions/glassfish/target/stage/glassfish7/glassfish/lib/client/appserver-cli.jar start-domain && java -jar /app/glassfish/appserver/distributions/glassfish/target/stage/glassfish7/glassfish/lib/client/appserver-cli.jar deploy /app/garden_webapp && sed -e 's/8080/80/g' -e 's/"\/garden_webapp"/"\/"/g' -i /app/glassfish/appserver/distributions/glassfish/target/stage/glassfish7/glassfish/domains/domain1/config/domain.xml && rm /app/glassfish/appserver/distributions/glassfish/target/stage/glassfish7/glassfish/domains/domain1/docroot/index.html

CMD java -jar /app/glassfish/appserver/distributions/glassfish/target/stage/glassfish7/glassfish/lib/client/appserver-cli.jar start-domain && sleep infinity
