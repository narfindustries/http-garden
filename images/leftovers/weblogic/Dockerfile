FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends unzip wget libx11-dev libxext-dev libxi-dev libxrender-dev libxtst-dev

COPY weblogic.zip .

RUN wget 'https://download.oracle.com/java/24/latest/jdk-24_linux-x64_bin.deb' && dpkg -i *.deb && unzip weblogic.zip

RUN useradd --create-home user && chown user:user /app/*.jar
USER user

RUN yes | java -Djava.awt.headless=true -jar *.jar
