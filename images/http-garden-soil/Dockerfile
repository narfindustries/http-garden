FROM debian:trixie-slim

WORKDIR /app

ENV DEBIAN_FRONTEND='noninteractive'

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends make clang-19 llvm-19-dev lld-19 git gcc-14-plugin-dev libclang-rt-19-dev gcc-14 g++-14 busybox vim ncat ca-certificates less pkg-config autoconf-archive automake libssl-dev zlib1g-dev libzstd-dev

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-19 100 \
 && update-alternatives --install /usr/bin/cc cc /usr/bin/clang-19 100 \
 && update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-19 100 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-19 100 \
 && update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-19 100 \
 && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-14 100 \
 && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-14 100 \
 && update-alternatives --install "/usr/bin/$(uname -m)-linux-gnu-gcc" "$(uname -m)-linux-gnu-gcc" "/usr/bin/$(uname -m)-linux-gnu-gcc-14" 100 \
 && ln -sf "/usr/lib/llvm-19/lib/clang/19/lib/linux/libclang_rt.ubsan_standalone_cxx-$(uname -m).a" /usr/lib/libclang_rt.ubsan_standalone_cxx.a \
 && ln -sf "/usr/lib/llvm-19/lib/clang/19/lib/linux/libclang_rt.ubsan_standalone-$(uname -m).a" /usr/lib/libclang_rt.ubsan_standalone.a

ENV CC='clang'
ENV CXX='clang++'
ENV LDFLAGS='-fsanitize=address,undefined,nullability-arg,nullability-assign,nullability-return'
ENV CFLAGS="-g -O0 $LDFLAGS -fno-sanitize=function,alignment -fsanitize-address-use-after-scope -fno-sanitize-recover=all"
ENV CXXFLAGS="$CFLAGS"

ENV UBSAN_OPTIONS='print_stacktrace=1'
ENV ASAN_OPTIONS='detect_stack_use_after_return=1:detect_leaks=0'

ARG CPYTHON_REPO
ARG CPYTHON_BRANCH
ARG CPYTHON_VERSION
RUN git clone --recurse-submodules "$CPYTHON_REPO" \
 && cd /app/cpython \
 && git pull origin "$CPYTHON_BRANCH" \
 && git checkout "$CPYTHON_VERSION" \
 && ./configure \
 && make "-j$(nproc)"

RUN /app/cpython/python -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt -y autoremove && rm -rf /var/lib/apt/lists/*
