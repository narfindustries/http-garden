FROM http-garden-soil:latest

RUN apt -y update && apt -y install --no-install-recommends curl gpg unzip openjdk-21-jdk libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

ARG APP_VERSION
RUN cd /app/ktor && git pull && git checkout "$APP_VERSION" && ./gradlew assemble --no-scan -x test -x compileProductionLibraryKotlinJs -x compileKotlinJs -x compileKotlinWasmJs

RUN curl -L 'https://github.com/JetBrains/kotlin/releases/download/v2.1.0/kotlin-compiler-2.1.0.zip' -o kotlinc.zip && unzip kotlinc.zip && rm kotlinc.zip

COPY Application.kt /app

RUN ls /root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlinx/kotlinx-io-core-jvm > kotlinx-io-core-jvm-version \
 && echo /app/ktor/ktor-client/build/libs/ktor-client-jvm-*.jar | sed -e 's/^\/app\/ktor\/ktor-client\/build\/libs\/ktor-client-jvm-//' -e 's/\.jar$//' > ktor-version

RUN ./kotlinc/bin/kotlinc -cp ./ktor/ktor-server/ktor-server-core/build/libs/ktor-server-core-jvm-$(cat ktor-version).jar:./kotlinc/lib/kotlinx-coroutines-core-jvm.jar:./ktor/ktor-server/ktor-server-cio/build/libs/ktor-server-cio-jvm-$(cat ktor-version).jar:./ktor/ktor-utils/build/libs/ktor-utils-jvm-$(cat ktor-version).jar:$(find /root -name 'kotlinx-io-core-jvm-*.jar' | head -n 1):./kotlinc/lib/kotlin-main-kts.jar:./ktor/ktor-shared/ktor-events/build/libs/ktor-events-jvm-$(cat ktor-version).jar:./ktor/ktor-http/build/libs/ktor-http-jvm-$(cat ktor-version).jar:./ktor/ktor-network/build/libs/ktor-network-jvm-$(cat ktor-version).jar -include-runtime -d Application.jar Application.kt

CMD java -cp Application.jar:./ktor/ktor-server/ktor-server-core/build/libs/ktor-server-core-jvm-$(cat ktor-version).jar:./kotlinc/lib/kotlinx-coroutines-core-jvm.jar:./ktor/ktor-server/ktor-server-cio/build/libs/ktor-server-cio-jvm-$(cat ktor-version).jar:./ktor/ktor-utils/build/libs/ktor-utils-jvm-$(cat ktor-version).jar:$(find /root -name 'kotlinx-io-core-jvm-*.jar' | head -n 1):./kotlinc/lib/kotlin-main-kts.jar:./ktor/ktor-shared/ktor-events/build/libs/ktor-events-jvm-$(cat ktor-version).jar:./ktor/ktor-http/build/libs/ktor-http-jvm-$(cat ktor-version).jar:./ktor/ktor-network/build/libs/ktor-network-jvm-$(cat ktor-version).jar:./ktor/ktor-io/build/libs/ktor-io-jvm-$(cat ktor-version).jar:./ktor/ktor-http/ktor-http-cio/build/libs/ktor-http-cio-jvm-$(cat ktor-version).jar com.example.ApplicationKt
