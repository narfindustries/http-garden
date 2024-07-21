FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends curl unzip openjdk-22-jdk

# tried for a long time to get Ktor to build from source. Eventually, I gave up and submitted this issue: https://youtrack.jetbrains.com/issue/KTOR-7225/Debian-build-failures-due-to-undetected-toolchain
# What we do now is fill out the form at start.ktor.io, grab the resulting zipfile, and transplant in our own Routing.kt

ARG APP_VERSION
RUN mkdir ktor && cd ktor && curl -X POST -H 'Content-Type: application/json' --data '{"settings":{"project_name":"com.example.ktor-sample","company_website":"com.example","ktor_version":"'"$APP_VERSION"'","kotlin_version":"2.0.0","build_system":"GRADLE_KTS","engine":"CIO"},"features":[],"configurationOption":"YAML","addDefaultRoutes":true,"addWrapper":true}' https://start.ktor.io/project/generate > ktor.zip && unzip ktor.zip

RUN cd /app/ktor && ./gradlew build

COPY Routing.kt /app/ktor/src/main/kotlin/example/com/plugins/Routing.kt

# This happens twice so we don't need to rebuild everything just to update the application
RUN cd /app/ktor && ./gradlew build

CMD java -jar /app/ktor/build/libs/com.example.ktor-sample-all.jar -port=80
