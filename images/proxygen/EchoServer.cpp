/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

#include <folly/Memory.h>
#include <folly/io/async/EventBaseManager.h>
#include <folly/portability/Unistd.h>
#include <proxygen/httpserver/HTTPServer.h>
#include <proxygen/httpserver/RequestHandlerFactory.h>

#include "EchoHandler.h"

using namespace EchoService;
using namespace proxygen;

using folly::SocketAddress;

using Protocol = HTTPServer::Protocol;

class EchoHandlerFactory : public RequestHandlerFactory {
 public:
  void onServerStart(folly::EventBase* /*evb*/) noexcept override {
  }

  void onServerStop() noexcept override {
  }

  RequestHandler* onRequest(RequestHandler*, HTTPMessage*) noexcept override {
    return new EchoHandler();
  }
};

int main(int argc, char* argv[]) {
  std::vector<HTTPServer::IPConfig> IPs = {
      {SocketAddress("0.0.0.0", 80, true), Protocol::HTTP},
  };

  HTTPServerOptions options;
  options.threads = static_cast<size_t>(1);
  options.idleTimeout = std::chrono::milliseconds(60000);
  options.shutdownOn = {SIGINT, SIGTERM};
  options.enableContentCompression = false;
  options.handlerFactories =
      RequestHandlerChain().addThen<EchoHandlerFactory>().build();
  // Increase the default flow control to 1MB/10MB
  options.initialReceiveWindow = uint32_t(1 << 20);
  options.receiveStreamWindowSize = uint32_t(1 << 20);
  options.receiveSessionWindowSize = 10 * (1 << 20);
  options.h2cEnabled = false;

  HTTPServer server(std::move(options));
  server.bind(IPs);

  // Start HTTPServer mainloop in a separate thread
  std::thread t([&]() { server.start(); });

  t.join();
  return 0;
}
