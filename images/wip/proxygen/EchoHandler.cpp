/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

#include <string>

#include "EchoHandler.h"

#include <folly/Memory.h>
#include <folly/base64.h>
#include <proxygen/httpserver/RequestHandler.h>
#include <proxygen/httpserver/ResponseBuilder.h>

using namespace proxygen;

namespace EchoService {

EchoHandler::EchoHandler() {
  body_ = nullptr;
  req_ = nullptr;
}

void EchoHandler::onRequest(std::unique_ptr<HTTPMessage> req) noexcept {
  req_ = std::move(req);
}

void EchoHandler::onBody(std::unique_ptr<folly::IOBuf> body) noexcept {
  if (body_ != nullptr) {
    body_->appendToChain(std::move(body));
  } else {
    body_ = std::move(body);
  }
}

void EchoHandler::onEOM() noexcept {
  std::unique_ptr<folly::IOBuf> buf = folly::IOBuf::copyBuffer("{\"method\":\"");
  buf->appendToChain(folly::IOBuf::copyBuffer(folly::base64Encode(req_->getMethodString())));
  buf->appendToChain(folly::IOBuf::copyBuffer("\",\"version\":\""));
  buf->appendToChain(folly::IOBuf::copyBuffer(folly::base64Encode(req_->getVersionString())));
  buf->appendToChain(folly::IOBuf::copyBuffer("\",\"uri\":\""));
  buf->appendToChain(folly::IOBuf::copyBuffer(folly::base64Encode(req_->getURL())));
  buf->appendToChain(folly::IOBuf::copyBuffer("\",\"headers\":["));
  bool first = true;
  req_->getHeaders().forEach([&](std::string& name, std::string& value) {
    if (!first) {
      buf->appendToChain(folly::IOBuf::copyBuffer(","));
    }
    buf->appendToChain(folly::IOBuf::copyBuffer("[\""));
    buf->appendToChain(folly::IOBuf::copyBuffer(folly::base64Encode(name)));
    buf->appendToChain(folly::IOBuf::copyBuffer("\",\""));
    buf->appendToChain(folly::IOBuf::copyBuffer(folly::base64Encode(value)));
    buf->appendToChain(folly::IOBuf::copyBuffer("\"]"));
    first = false;
  });
  buf->appendToChain(folly::IOBuf::copyBuffer("],\"body\":\""));
  std::string body_str;
  if (body_) {
    for (auto const &chunk : *body_) {
      body_str.append(chunk.begin(), chunk.end());
    }
    buf->appendToChain(folly::IOBuf::copyBuffer(folly::base64Encode(body_str)));
  }
  buf->appendToChain(folly::IOBuf::copyBuffer("\"}"));

  ResponseBuilder(downstream_)
      .status(200, "OK")
      .body(std::move(buf))
      .sendWithEOM();
}

void EchoHandler::onUpgrade(UpgradeProtocol /*protocol*/) noexcept {
  // handler doesn't support upgrades
}

void EchoHandler::requestComplete() noexcept {
  delete this;
}

void EchoHandler::onError(ProxygenError /*err*/) noexcept {
  delete this;
}
} // namespace EchoService
