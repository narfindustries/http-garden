//
// Copyright (c) 2016-2019 Vinnie Falco (vinnie dot falco at gmail dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// Official repository: https://github.com/boostorg/beast
//

//------------------------------------------------------------------------------
//
// Example: HTTP server, synchronous
// Modified by Ben K @ Narf
//
//------------------------------------------------------------------------------

#include <boost/asio/ip/tcp.hpp>
#include <boost/beast/core.hpp>
#include <boost/beast/http.hpp>
#include <boost/beast/http/verb.hpp>
#include <boost/beast/version.hpp>
#include <boost/beast/core/detail/base64.hpp>
#include <boost/config.hpp>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>
#include <thread>

namespace beast = boost::beast;          // from <boost/beast.hpp>
namespace detail = boost::beast::detail; // from <boost/beast/core/detail/base64.hpp>
namespace http = beast::http;            // from <boost/beast/http.hpp>
namespace net = boost::asio;             // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp;        // from <boost/asio/ip/tcp.hpp>

//------------------------------------------------------------------------------

// Return a response for the given request.
//
// The concrete type of the response message (which depends on the
// request), is type-erased in message_generator.
template <class Allocator>
http::message_generator handle_request(http::request<http::string_body, http::basic_fields<Allocator>> &&req) {
    // Returns a bad request response
    auto const bad_request = [&req](beast::string_view why) {
        http::response<http::string_body> res{http::status::bad_request, req.version()};
        res.set(http::field::server, BOOST_BEAST_VERSION_STRING);
        res.set(http::field::content_type, "text/html");
        res.keep_alive(req.keep_alive());
        res.body() = std::string(why);
        res.prepare_payload();
        return res;
    };

    // Make sure we can handle the method
    if (req.method() == http::verb::unknown)
        return bad_request("Unknown HTTP-method");

    // Respond to request
    http::response<http::dynamic_body> res;
    res.set(http::field::server, BOOST_BEAST_VERSION_STRING);

    // Extract headers and base64-encode them
    beast::ostream(res.body()) << "{\"headers\":[";
    bool first = true;
    for (auto const &header : req.base()) {
        char *name_b64 = new char[detail::base64::encoded_size(header.name_string().length()) + 1];
        name_b64[detail::base64::encode(name_b64, header.name_string().data(), header.name_string().length())] = '\0';
        char *value_b64 = new char[detail::base64::encoded_size(header.value().length()) + 1];
        value_b64[detail::base64::encode(value_b64, header.value().data(), header.value().length())] = '\0';

        beast::ostream(res.body()) << (first ? "" : ",") << "[\"" << name_b64 << "\",\"" << value_b64 << "\"]";
        delete[] name_b64;
        delete[] value_b64;
        if (first) {
            first = false;
        }
    }

    // Extract body and base64-encode it
    char *body_b64 = new char[detail::base64::encoded_size(req.body().length()) + 1];
    body_b64[detail::base64::encode(body_b64, req.body().c_str(), req.body().length())] = '\0';
    beast::ostream(res.body()) << "],\"body\":\"" << body_b64 << "\",";

    char *method_b64 = new char[detail::base64::encoded_size(to_string(req.method()).length()) + 1];
    method_b64[detail::base64::encode(method_b64, to_string(req.method()).data(), to_string(req.method()).length())] = '\0';
    beast::ostream(res.body()) << "\"method\":\"" << method_b64 << "\",";

    std::string version = std::string("HTTP/") + std::to_string(req.version() / 10) + std::string(".") + std::to_string(req.version() % 10);
    char *version_b64 = new char[detail::base64::encoded_size(version.length()) + 1];
    version_b64[detail::base64::encode(version_b64, version.c_str(), version.length())] = '\0';
    beast::ostream(res.body()) << "\"version\":\"" << version_b64 << "\",";

    char *path_b64 = new char[detail::base64::encoded_size(req.target().length()) + 1];
    path_b64[detail::base64::encode(path_b64, req.target().data(), req.target().length())] = '\0';
    beast::ostream(res.body()) << "\"uri\":\"" << path_b64 << "\"}";

    res.keep_alive(req.keep_alive());
    res.prepare_payload();
    delete[] body_b64;
    delete[] method_b64;
    delete[] path_b64;

    return res;
}

//------------------------------------------------------------------------------

// Report a failure
void fail(beast::error_code ec, char const *what) {
    std::cerr << what << ": " << ec.message() << "\n";
}

// Handles an HTTP server connection
void do_session(tcp::socket &socket) {
    beast::error_code ec;

    // This buffer is required to persist across reads
    beast::flat_buffer buffer;

    http::response<http::string_body> error_msg{http::status::bad_request, 11}; // The 11 is for HTTP/1.1
    error_msg.set(http::field::server, BOOST_BEAST_VERSION_STRING);
    error_msg.set(http::field::content_type, "text/html");
    error_msg.keep_alive(false);
    error_msg.prepare_payload();
    http::message_generator error_msg_generator(std::move(error_msg));

    for (;;) {
        // Read a request
        http::request<http::string_body> req;
        http::read(socket, buffer, req, ec);
        if (ec == http::error::end_of_stream) {
            break;
        } else if (ec) {
            beast::write(socket, error_msg_generator, ec);
            if (ec) {
                return fail(ec, "write error");
            }
        } else {
            // Handle request
            http::message_generator msg = handle_request(std::move(req));

            // Determine if we should close the connection
            bool keep_alive = msg.keep_alive();

            // Send the response
            beast::write(socket, std::move(msg), ec);

            if (ec) {
                return fail(ec, "write");
            } else if (!keep_alive) {
                // This means we should close the connection, usually because
                // the response indicated the "Connection: close" semantic.
                break;
            }
        }
    }

    // Send a TCP shutdown
    socket.shutdown(tcp::socket::shutdown_send, ec);

    // At this point the connection is closed gracefully
}

//------------------------------------------------------------------------------

int main(int argc, char *argv[]) {
    try {
        // Check command line arguments.
        if (argc != 3) {
            std::cerr << "Usage: http-server-sync <address> <port>\n"
                      << "Example:\n"
                      << "    http-server-sync 0.0.0.0 8080 .\n";
            return EXIT_FAILURE;
        }
        auto const address = net::ip::make_address(argv[1]);
        auto const port = static_cast<unsigned short>(std::atoi(argv[2]));

        // The io_context is required for all I/O
        net::io_context ioc{1};

        // The acceptor receives incoming connections
        tcp::acceptor acceptor{ioc, {address, port}};
        for (;;) {
            // This will receive the new connection
            tcp::socket socket{ioc};

            // Block until we get a connection
            acceptor.accept(socket);

            // Launch the session, transferring ownership of the socket
            std::thread{std::bind(&do_session, std::move(socket))}.detach();
        }
    } catch (const std::exception &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return EXIT_FAILURE;
    }
}
