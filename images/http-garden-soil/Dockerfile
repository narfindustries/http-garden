FROM debian:trixie-slim

WORKDIR /app

RUN apt -y update && apt -y upgrade && apt -y install make clang-17 llvm-17-dev lld-17 git python3-dev cython3 gcc-13-plugin-dev libclang-rt-17-dev gcc-13 g++-13 busybox vim ncat

RUN git clone --recurse-submodules 'https://github.com/jwilk/python-afl' && cd python-afl && python3 setup.py install
ENV PYTHON_AFL_SIGNAL=0

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-17 100 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-17 100 \
 && update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-17 100 \
 && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 \
 && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100

RUN git clone --recurse-submodules 'https://github.com/kenballus/AFLplusplus' && cd AFLplusplus && make -j$(nproc) && make install

RUN ln -s /usr/local/bin/afl-cc /usr/bin/afl-c++

ENV AFL_CC_COMPILER=LTO
ENV AFL_PATH=/app/AFLplusplus

RUN rm -rf /var/lib/apt/lists/*
