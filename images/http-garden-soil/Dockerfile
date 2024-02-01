FROM debian:bookworm-slim

WORKDIR /app

RUN apt -y update && apt -y upgrade && apt -y install make clang-16 llvm-16-dev lld-16 git python3-dev cython3 gcc-12-plugin-dev libclang-rt-16-dev gcc g++ busybox vim ncat

RUN git clone 'https://github.com/jwilk/python-afl' && cd python-afl && python3 setup.py install
ENV PYTHON_AFL_SIGNAL=0

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-16 100 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-16 100 \
 && update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-16 100

RUN git clone 'https://github.com/kenballus/AFLplusplus' && cd AFLplusplus && make -j$(nproc) && make install

RUN ln -s /usr/local/bin/afl-cc /usr/bin/afl-c++

ENV AFL_CC_COMPILER=LTO
ENV AFL_PATH=/app/AFLplusplus

RUN rm -rf /var/lib/apt/lists/*
