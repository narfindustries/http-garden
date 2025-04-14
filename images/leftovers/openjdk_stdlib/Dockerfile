FROM http-garden-soil:latest

WORKDIR /app
RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends autoconf file unzip zip openjdk-24-jdk libasound2-dev libcups2-dev libfontconfig1-dev libx11-dev libxext-dev libxrender-dev libxrandr-dev libxtst-dev libxt-dev

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_BRANCH
ARG APP_VERSION
RUN cd /app/jdk \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && bash configure \
 && make images JOBS=$(nproc)

COPY GardenServer.java .
RUN /app/jdk/build/linux-x86_64-server-release/images/jdk/bin/javac GardenServer.java

CMD ["/app/jdk/build/linux-x86_64-server-release/images/jdk/bin/java", "-cp", ".", "GardenServer"]
