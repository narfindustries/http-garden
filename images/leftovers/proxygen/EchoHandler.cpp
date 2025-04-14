/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 *
 * Modified heavily by Ben Kallus
 */

#include <apr-1.0/apr_encode.h>
#include <folly/Memory.h>
#include <folly/io/async/EventBaseManager.h>
#include <folly/portability/Unistd.h>
#include <proxygen/httpserver/HTTPServer.h>
#include <proxygen/httpserver/RequestHandler.h>
#include <proxygen/httpserver/RequestHandlerFactory.h>
#include <proxygen/httpserver/ResponseBuilder.h>

class EchoHandler : public proxygen::RequestHandler {
  public:
    explicit EchoHandler();

    void onRequest(std::unique_ptr<proxygen::HTTPMessage>) noexcept override;

    void onBody(std::unique_ptr<folly::IOBuf>) noexcept override;

    void onEOM() noexcept override;

    void onUpgrade(proxygen::UpgradeProtocol) noexcept override;

    void requestComplete() noexcept override;

    void onError(proxygen::ProxygenError) noexcept override;
};

EchoHandler::EchoHandler() {
}

void EchoHandler::onRequest(
    std::unique_ptr<proxygen::HTTPMessage> req) noexcept {
    proxygen::ResponseBuilder builder(downstream_);
    builder.status(200, "OK");
    req->getHeaders().forEach([&](std::string &name, std::string &value) {
        builder.header(folly::to<std::string>("x-echo-", name), value);
    });
    builder.send();
}

void EchoHandler::onBody(std::unique_ptr<folly::IOBuf> body) noexcept {
    proxygen::ResponseBuilder(downstream_).body(std::move(body)).send();
}

void EchoHandler::onEOM() noexcept {
    proxygen::ResponseBuilder(downstream_).sendWithEOM();
}

void EchoHandler::onUpgrade(proxygen::UpgradeProtocol) noexcept {
}

void EchoHandler::requestComplete() noexcept {
    delete this;
}

void EchoHandler::onError(proxygen::ProxygenError) noexcept {
    delete this;
}

class EchoHandlerFactory : public proxygen::RequestHandlerFactory {
  public:
    void onServerStart(folly::EventBase *) noexcept override {
    }

    void onServerStop() noexcept override {
    }

    proxygen::RequestHandler *
    onRequest(proxygen::RequestHandler *,
              proxygen::HTTPMessage *) noexcept override {
        return new EchoHandler();
    }
};

int main(void) {
    proxygen::HTTPServerOptions options;
    options.threads = static_cast<size_t>(1);
    options.handlerFactories =
        proxygen::RequestHandlerChain().addThen<EchoHandlerFactory>().build();

    proxygen::HTTPServer server(std::move(options));
    server.bind({{folly::SocketAddress("0.0.0.0", 80, true),
                  proxygen::HTTPServer::Protocol::HTTP}});

    server.start();
}
