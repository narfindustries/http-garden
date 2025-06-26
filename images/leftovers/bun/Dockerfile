FROM ubuntu:23.10

WORKDIR /app

RUN apt -y update && apt -y upgrade && apt -y install git lsb-release gpg software-properties-common unzip curl wget cargo ccache cmake golang libtool ninja-build pkg-config rustc esbuild ruby && curl -fsSL https://bun.sh/install | bash && wget https://apt.llvm.org/llvm.sh -O - | bash -s -- 16 all

RUN /root/.bun/bin/bun install -g @oven/zig && git clone 'https://github.com/oven-sh/bun'

ARG APP_VERSION
RUN cd /app/bun && git checkout "$APP_VERSION" && export PATH="$PATH:/root/.bun/bin/" && bun run build && cp ./build/bun-debug /bin/bun

COPY app.js /app/
CMD ["/bin/bun", "app.js"]
