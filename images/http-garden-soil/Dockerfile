FROM debian:trixie-slim

WORKDIR /app

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends make clang-17 llvm-17-dev lld-17 git python3-dev python3-setuptools cython3 gcc-13-plugin-dev libclang-rt-17-dev gcc-13 g++-13 busybox vim ncat ca-certificates python3-pip
RUN git clone --recurse-submodules 'https://github.com/jwilk/python-afl' && git clone 'https://github.com/kenballus/AFLplusplus'

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-17 100 \
 && update-alternatives --install /usr/bin/cc cc /usr/bin/clang-17 100 \
 && update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-17 100 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-17 100 \
 && update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-17 100 \
 && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 \
 && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100 \
 && update-alternatives --install /usr/bin/x86_64-linux-gnu-gcc x86_64-linux-gnu-gcc /usr/bin/x86_64-linux-gnu-gcc-13 100

RUN cd python-afl && pip install . --break-system-packages

RUN cd AFLplusplus && make -j"$(nproc)" && make install

RUN ln -s /usr/local/bin/afl-cc /usr/bin/afl-c++

ENV PYTHON_AFL_SIGNAL=0
ENV AFL_CC_COMPILER=LTO
ENV AFL_PATH=/app/AFLplusplus
ENV ASAN_OPTIONS='detect_stack_use_after_return=true'
ENV AFL_DEBUG=1

RUN rm -rf /var/lib/apt/lists/*
