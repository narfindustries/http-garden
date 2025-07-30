FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y install --no-install-recommends curl gpg unzip openjdk-21-jdk libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/ktor \
 && export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-$(dpkg --print-architecture)" \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./gradlew :ktor-server-cio:jvmJar :ktor-server-core:jvmJar :ktor-utils:jvmJar :ktor-events:jvmJar :ktor-http:jvmJar :ktor-network:jvmJar :ktor-io:jvmJar

ARG KOTLIN_COMPILER_ZIP_URL
RUN curl -L "$KOTLIN_COMPILER_ZIP_URL" -o kotlinc.zip \
 && unzip kotlinc.zip \
 && rm kotlinc.zip

COPY Application.kt /app

RUN ls /root/.gradle/caches/modules*/files-2.1/org.jetbrains.kotlinx/kotlinx-io-core-jvm | cut -d' ' -f1 > kotlinx-io-core-jvm-version \
 && echo /app/ktor/ktor-server/ktor-server-core/build/libs/ktor-server-core-jvm-*.jar | sed -e 's/^\/app\/ktor\/ktor-server\/ktor-server-core\/build\/libs\/ktor-server-core-jvm-//' -e 's/\.jar$//' > ktor-version

RUN ./kotlinc/bin/kotlinc -cp ./ktor/ktor-server/ktor-server-core/build/libs/ktor-server-core-jvm-$(cat ktor-version).jar:./kotlinc/lib/kotlinx-coroutines-core-jvm.jar:./ktor/ktor-server/ktor-server-cio/build/libs/ktor-server-cio-jvm-$(cat ktor-version).jar:./ktor/ktor-utils/build/libs/ktor-utils-jvm-$(cat ktor-version).jar:$(find /root -name 'kotlinx-io-core-jvm-*.jar' | head -n 1):./kotlinc/lib/kotlin-main-kts.jar:./ktor/ktor-shared/ktor-events/build/libs/ktor-events-jvm-$(cat ktor-version).jar:./ktor/ktor-http/build/libs/ktor-http-jvm-$(cat ktor-version).jar:./ktor/ktor-network/build/libs/ktor-network-jvm-$(cat ktor-version).jar -include-runtime -d Application.jar Application.kt

CMD java -cp Application.jar:./ktor/ktor-server/ktor-server-core/build/libs/ktor-server-core-jvm-$(cat ktor-version).jar:./kotlinc/lib/kotlinx-coroutines-core-jvm.jar:./ktor/ktor-server/ktor-server-cio/build/libs/ktor-server-cio-jvm-$(cat ktor-version).jar:./ktor/ktor-utils/build/libs/ktor-utils-jvm-$(cat ktor-version).jar:$(find /root -name 'kotlinx-io-core-jvm-*.jar' | head -n 1):./kotlinc/lib/kotlin-main-kts.jar:./ktor/ktor-shared/ktor-events/build/libs/ktor-events-jvm-$(cat ktor-version).jar:./ktor/ktor-http/build/libs/ktor-http-jvm-$(cat ktor-version).jar:./ktor/ktor-network/build/libs/ktor-network-jvm-$(cat ktor-version).jar:./ktor/ktor-io/build/libs/ktor-io-jvm-$(cat ktor-version).jar:./ktor/ktor-http/ktor-http-cio/build/libs/ktor-http-cio-jvm-$(cat ktor-version).jar com.example.ApplicationKt
