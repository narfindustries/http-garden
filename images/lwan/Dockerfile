FROM http-garden-soil:latest

RUN apt -y update && \
	apt -y upgrade && \
	apt -y --no-install-recommends install \
		cmake zlib1g-dev libbrotli-dev libzstd-dev \
		build-essential ninja-build \
		liblua5.1-0-dev pkgconf-bin && \
	git clone "https://github.com/lpereira/lwan.git"

ARG APP_VERSION
RUN cd lwan && git checkout $APP_VERSION
RUN cd lwan && \
	mkdir build && \
	cd build && \
	cmake .. -DCMAKE_C_COMPILER='afl-cc' \
		-DSANITIZER=address \
		-GNinja && \
	ninja lwan && \
	cp src/bin/lwan/lwan /app/lwan/lwan

COPY base64.lua /app/lwan
COPY json.lua /app/lwan
COPY lwan.conf /app/lwan

ENV AFL_DEBUG=1
ENV ASAN_OPTIONS='detect_stack_use_after_return=true'
CMD ["afl-showmap", "-o", "/tmp/trace", "-t", "2147483647", "--", "/app/lwan/lwan", "-c", "/app/lwan/lwan.conf"]
