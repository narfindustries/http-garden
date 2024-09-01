FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends ruby-rubygems

ARG APP_REPO
RUN git clone --recurse-submodules "$APP_REPO"

ARG APP_VERSION
RUN cd protocol-http1 && git pull && git checkout "$APP_VERSION" && sed -e 's/spec.cert.chain/#spec.cert.chain/' -e 's/spec.signing_key/#spec.signing_key/' -i protocol-http1.gemspec && gem build && gem install ./*.gem

COPY server.rb .
CMD ["ruby", "server.rb"]
