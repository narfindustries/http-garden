FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends cmake golang libapr1-dev

ARG APP_REPO
ARG AWS_LC_REPO
ARG S2N_TLS_REPO
ARG AWS_C_COMMON_REPO
ARG AWS_C_CAL_REPO
ARG AWS_C_IO_REPO
ARG AWS_C_COMPRESSION_REPO
RUN git clone --recurse-submodules "$APP_REPO" \
 && git clone --recurse-submodules "$AWS_LC_REPO" \
 && git clone --recurse-submodules "$S2N_TLS_REPO" \
 && git clone --recurse-submodules "$AWS_C_COMMON_REPO" \
 && git clone --recurse-submodules "$AWS_C_CAL_REPO" \
 && git clone --recurse-submodules "$AWS_C_IO_REPO" \
 && git clone --recurse-submodules "$AWS_C_COMPRESSION_REPO"

ARG AWS_LC_VERSION
RUN cd aws-lc \
 && git checkout "$AWS_LC_VERSION" \
 && unset CC CXX \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make "-j$(nproc)" install

ARG S2N_TLS_VERSION
RUN cd s2n-tls \
 && git checkout "$S2N_TLS_VERSION" \
 && unset CC CXX \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make "-j$(nproc)" install

# Note that we disable CXXFLAGS here because the use of hash_eq is UB without casting.
ARG AWS_C_COMMON_VERSION
RUN cd aws-c-common \
 && git checkout "$AWS_C_COMMON_VERSION" \
 && unset CC CFLAGS CXXFLAGS CXX \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make "-j$(nproc)" install

ARG AWS_C_CAL_VERSION
RUN cd aws-c-cal \
 && git checkout "$AWS_C_CAL_VERSION" \
 && unset CC CXX \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make "-j$(nproc)" install

ARG AWS_C_IO_VERSION
RUN cd aws-c-io \
 && git checkout "$AWS_C_IO_VERSION" \
 && unset CC CXX \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make "-j$(nproc)" install

ARG AWS_C_COMPRESSION_VERSION
RUN cd aws-c-compression \
 && git checkout "$AWS_C_COMPRESSION_VERSION" \
 && unset CC CXX \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make "-j$(nproc)" install

ARG APP_VERSION
RUN cd aws-c-http \
 && git checkout "$APP_VERSION" \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make "-j$(nproc)" install

COPY server.c .
RUN "$CC" $CFLAGS -std=c23 server.c -Wno-incompatible-pointer-types-discards-qualifiers /usr/local/lib/libaws-c-http.a /usr/local/lib/libaws-c-common.a /usr/local/lib/libaws-c-compression.a /usr/local/lib/libaws-c-io.a /usr/local/lib/libs2n.a /usr/local/lib/libcrypto.a /usr/local/lib/libssl.a /usr/local/lib/libaws-c-cal.a -o server -lapr-1

CMD ["./server"]
