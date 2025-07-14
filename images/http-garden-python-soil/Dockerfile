FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade \
 && apt -y install --no-install-recommends pkg-config autoconf-archive automake libssl-dev zlib1g-dev libzstd-dev

ARG CPYTHON_REPO
ARG CPYTHON_BRANCH
ARG CPYTHON_VERSION
RUN git clone --recurse-submodules "$CPYTHON_REPO" \
 && cd /app/cpython \
 && git pull origin "$CPYTHON_BRANCH" \
 && git checkout "$CPYTHON_VERSION" \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && ./configure \
 && make "-j$(nproc)"

RUN /app/cpython/python -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
