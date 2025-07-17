FROM http-garden-soil:latest

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

# Disable sanitizers because UBSan is tripped during the build process.
ARG APP_VERSION
ARG APP_BRANCH
RUN cd /app/node \
 && unset CC CXX CFLAGS CXXFLAGS LDFLAGS \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION" \
 && ./configure \
 && make "-j$(nproc)"

ARG SCRIPT
COPY $SCRIPT /app/app.js

CMD ["/app/node/node", "app.js"]
