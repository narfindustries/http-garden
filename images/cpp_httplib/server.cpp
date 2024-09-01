#include <httplib.h> // for httplib
#include <cassert>
#include <cstdlib> // for malloc, NULL, free
#include <string> // for std::string
#include <apr-1.0/apr_encode.h> // for apr_encode_base64, APR_ENCODE_NONE

// Base64-encodes some data.
static std::string base64_encode(std::string const s) {
    size_t result_len;
    apr_encode_base64(NULL, s.c_str(), s.size(), APR_ENCODE_NONE, &result_len);

    char *result = (char *)malloc(result_len);
    assert(result != NULL);
    apr_encode_base64(result, s.c_str(), s.size(), APR_ENCODE_NONE, NULL);

    std::string result_str(result);
    free(result);
    return result_str;
}

void handler_with_content_reader(httplib::Request const &req, httplib::Response &res, httplib::ContentReader const &content_reader) {
    std::string result;
    result += std::string("{\"method\":\"") + base64_encode(req.method) + std::string("\",\"uri\":\"") + base64_encode(req.path) + std::string("\",\"version\":\"") + base64_encode(req.version) + std::string("\",\"headers\":[");
    bool first = true;
    for (auto const &[key, val] : req.headers) {
        if (key == std::string("REMOTE_PORT") || key == std::string("REMOTE_ADDR") || key == std::string("LOCAL_PORT") || key == std::string("LOCAL_ADDR")) {
            continue;
        }
        if (!first) {
            result += std::string(",");
        }
        first = false;
        result += std::string("[\"") + base64_encode(key) + std::string("\",\"") + base64_encode(val) + std::string("\"]");
    }
    result += std::string("],\"body\":\"");
    std::string body;
    content_reader([&](char const * const data, size_t const data_length) {
        body.append(data, data_length);
        return true;
    });
    result += base64_encode(body) + std::string("\"}");
    res.set_content(result.c_str(), "application/json");
}

void handler(httplib::Request const &req, httplib::Response &res) {
    std::string result;
    result += std::string("{\"method\":\"") + base64_encode(req.method) + std::string("\",\"uri\":\"") + base64_encode(req.path) + std::string("\",\"version\":\"") + base64_encode(req.version) + std::string("\",\"headers\":[");

    bool first = true;
    for (auto const &[key, val] : req.headers) {
        if (key == std::string("REMOTE_PORT") || key == std::string("REMOTE_ADDR") || key == std::string("LOCAL_PORT") || key == std::string("LOCAL_ADDR")) {
            continue;
        }
        if (!first) {
            result += std::string(",");
        }
        first = false;
        result += std::string("[\"") + base64_encode(key) + std::string("\",\"") + base64_encode(val) + std::string("\"]");
    }
    result += std::string("],\"body\":\"\"}");
    res.set_content(result.c_str(), "application/json");
}

int main(void) {
    httplib::Server svr;

    svr.Get(".*", handler);
    svr.Post(".*", handler_with_content_reader);
    svr.Put(".*", handler_with_content_reader);
    svr.Patch(".*", handler_with_content_reader);
    svr.Delete(".*", handler_with_content_reader);
    svr.Options(".*", handler);

    svr.listen("0.0.0.0", 80);
}
