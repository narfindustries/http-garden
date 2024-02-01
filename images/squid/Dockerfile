FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install automake autoconf libtool libtool-bin && git clone 'https://github.com/squid-cache/squid'

ARG APP_VERSION
RUN cd /app/squid && git checkout $APP_VERSION && ./bootstrap.sh && export CC='afl-cc' LDFLAGS='-fsanitize=address,undefined' CFLAGS='-fsanitize=address,undefined' CXX='afl-c++' CXXFLAGS='-fsanitize=address,undefined' && ./configure --disable-esi && make -j$(nproc) && make install

COPY ./squid.conf /usr/local/squid/etc
ARG BACKEND
RUN sed -i "s/PROXY_BACKEND_PLACEHOLDER/$BACKEND/g" /usr/local/squid/etc/squid.conf && useradd squid && chown -R squid:squid /usr/local/squid

# Not tracing because squid mysteriously crashes when tracing is turned on
CMD export AFL_MAP_SIZE="$(AFL_DEBUG=1 afl-showmap -o /dev/null -t 2147483647 -- /usr/local/squid/sbin/squid -N 2>&1 | grep -oP '__afl_final_loc \d+' | tail -n 1 | awk '{print $2}')" \
 && rm -f /usr/local/squid/var/run/squid.pid \
 && /usr/local/squid/sbin/squid -N
