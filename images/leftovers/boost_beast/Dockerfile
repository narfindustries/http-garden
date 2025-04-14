FROM http-garden-soil:latest

RUN apt -y update \
 && apt -y upgrade
# && apt -y install --no-install-recommends

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd boost \
 && git pull origin "$APP_BRANCH" \
 && git checkout "$APP_VERSION"
