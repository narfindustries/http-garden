FROM debian:trixie-slim

WORKDIR /app

ENV DEBIAN_FRONTEND='noninteractive'

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends make clang-19 llvm-19-dev lld-19 git gcc-14-plugin-dev libclang-rt-19-dev gcc-14 g++-14 busybox vim ncat ca-certificates less

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-19 100 \
 && update-alternatives --install /usr/bin/cc cc /usr/bin/clang-19 100 \
 && update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-19 100 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-19 100 \
 && update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-19 100 \
 && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-14 100 \
 && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-14 100 \
 && update-alternatives --install /usr/bin/x86_64-linux-gnu-gcc x86_64-linux-gnu-gcc /usr/bin/x86_64-linux-gnu-gcc-14 100

RUN ln -s /usr/local/bin/afl-cc /usr/bin/afl-c++

# Install the forked AFLplusplus
ARG AFLPLUSPLUS_REPO
ARG AFLPLUSPLUS_BRANCH
ARG AFLPLUSPLUS_VERSION
# We are deliberately not recursing submodules here because we don't want Unicorn, QEMU, or Nyx.
RUN git clone "$AFLPLUSPLUS_REPO" \
 && cd AFLplusplus \
 && git pull origin "$AFLPLUSPLUS_BRANCH" \
 && git checkout "$AFLPLUSPLUS_VERSION" \
 && make "-j$(nproc)" \
 && make install \
 && rm -rf .git

ENV AFL_CC_COMPILER=LTO
ENV AFL_PATH=/app/AFLplusplus
ENV AFL_DEBUG=1

RUN git clone https://github.com/kenballus/sigsan && \
 cd sigsan && \
 make

# We no longer enable strict_string_checks because AFAICT it doesn't work with strndup, even though strndup doesn't need null termination
ENV ASAN_OPTIONS='detect_stack_use_after_return=1:check_initialization_order=1:strict_init_order=1'

ENV CC='afl-cc'
ENV CXX='afl-c++'
ENV CFLAGS='-g -O0 -fsanitize=address,undefined,nullability-arg,nullability-assign,nullability-return -fsanitize-address-use-after-scope -fno-sanitize-recover=all'
ENV CXXFLAGS="$CFLAGS"
ENV LDFLAGS='-fsanitize=address,undefined,nullability-arg,nullability-assign,nullability-return'

RUN apt -y autoremove && rm -rf /var/lib/apt/lists/*
