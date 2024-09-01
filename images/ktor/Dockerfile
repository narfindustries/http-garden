FROM http-garden-soil:latest

RUN apt -y update && apt -y install --no-install-recommends curl gpg && curl https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor > /etc/apt/trusted.gpg.d/adoptium.gpg && echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" > /etc/apt/sources.list.d/adoptium.list

ARG APP_REPO
RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends unzip temurin-17-jdk temurin-11-jdk temurin-8-jdk libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 && git clone --recurse-submodules "$APP_REPO"

ENV JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64

ARG APP_VERSION
RUN cd /app/ktor && git pull && git checkout "$APP_VERSION" && ./gradlew assemble -x test

RUN curl -L 'https://github.com/JetBrains/kotlin/releases/download/v2.0.10/kotlin-compiler-2.0.10.zip' -o kotlinc.zip && unzip kotlinc.zip && rm kotlinc.zip

COPY Application.kt /app

RUN ./kotlinc/bin/kotlinc -cp ./ktor/ktor-server/ktor-server-core/build/libs/ktor-server-core-jvm-3.0.0-rc-1-SNAPSHOT.jar:./kotlinc/lib/kotlinx-coroutines-core-jvm.jar:./ktor/ktor-server/ktor-server-cio/build/libs/ktor-server-cio-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-utils/build/libs/ktor-utils-jvm-3.0.0-rc-1-SNAPSHOT.jar:/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlinx/kotlinx-io-core-jvm/0.5.1/22bdb3f90f1796d283f616249d9241203adcd28f/kotlinx-io-core-jvm-0.5.1.jar:./kotlinc/lib/kotlin-main-kts.jar:./ktor/ktor-shared/ktor-events/build/libs/ktor-events-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-http/build/libs/ktor-http-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-network/build/libs/ktor-network-jvm-3.0.0-rc-1-SNAPSHOT.jar -include-runtime -d Application.jar Application.kt

CMD java -cp Application.jar:./ktor/ktor-server/ktor-server-core/build/libs/ktor-server-core-jvm-3.0.0-rc-1-SNAPSHOT.jar:./kotlinc/lib/kotlinx-coroutines-core-jvm.jar:./ktor/ktor-server/ktor-server-cio/build/libs/ktor-server-cio-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-utils/build/libs/ktor-utils-jvm-3.0.0-rc-1-SNAPSHOT.jar:/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlinx/kotlinx-io-core-jvm/0.5.1/22bdb3f90f1796d283f616249d9241203adcd28f/kotlinx-io-core-jvm-0.5.1.jar:./kotlinc/lib/kotlin-main-kts.jar:./ktor/ktor-shared/ktor-events/build/libs/ktor-events-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-http/build/libs/ktor-http-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-network/build/libs/ktor-network-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-io/build/libs/ktor-io-jvm-3.0.0-rc-1-SNAPSHOT.jar:./ktor/ktor-http/ktor-http-cio/build/libs/ktor-http-cio-jvm-3.0.0-rc-1-SNAPSHOT.jar com.example.ApplicationKt
