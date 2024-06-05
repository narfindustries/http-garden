#include <unistd.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "civetweb.h"

static size_t base64_encoded_len(size_t const plaintext_len) {
    // Base64-encoding takes 3n bytes to 4n bytes.
    // Then, there's padding, so we add on a correction term.
    // Note that we do not care about '\0' terminators here.
    return 4 * (plaintext_len / 3) + (plaintext_len % 3 != 0 ? 4 : 0);
}

#define INITIAL_BUF_SIZE (65535)
// *buf: A pointer to a heap-allocated buffer                      (might be `realloc`ed)
// *buf_size: The size of buf                                      (gets adjusted if *buf is `realloc`ed)
// *buf_size_remaining: The number of free bytes at the end of buf (gets adjusted if *buf is `realloc`ed)
// src: A buffer that we'll copy into buf
// src_size: The number of bytes to copy from src to buf.
void add_to_buffer(char **const buf_ptr, size_t *const buf_size_ptr, size_t *const buf_size_remaining_ptr,
 char const *const src, size_t const src_size) {
    char *buf = *buf_ptr;
    size_t buf_size = *buf_size_ptr;
    size_t buf_size_remaining = *buf_size_remaining_ptr;
    while (buf_size_remaining < src_size) {                              // Is there enough room?
        char *const new_buf = realloc(buf, buf_size + INITIAL_BUF_SIZE); // If not, make buf INITIAL_BUF_SIZE bigger.
        if (new_buf == NULL) {                                           // Did it work?
            puts("Out of memory!");
            exit(1);                                                     // If not, fail.
        }
        buf = new_buf;                                                   // Update buf and friends.
        buf_size += INITIAL_BUF_SIZE;
        buf_size_remaining += INITIAL_BUF_SIZE;
    }
    memcpy(buf + (buf_size - buf_size_remaining), src, src_size);        // Copy the data into the buffer
    buf_size_remaining -= src_size;

    *buf_ptr = buf;                                                      // Fill the in-out args
    *buf_size_ptr = buf_size;
    *buf_size_remaining_ptr = buf_size_remaining;
}

static char B64_SCRATCH_SPACE[INITIAL_BUF_SIZE];
static char STRCAT_SCRATCH_SPACE[INITIAL_BUF_SIZE];
static char const PAYLOAD_START[] =              "{\"headers\":[";
static char const PAYLOAD_FIRST_HEADER_START[] = "[\"";
static char const PAYLOAD_HEADER_START[] =       ",[\"";
static char const PAYLOAD_HEADER_MID[] =         "\",\"";
static char const PAYLOAD_HEADER_END[] =         "\"]";
static char const PAYLOAD_BODY_BEGIN[] =         "],\"body\":\"";
static char const PAYLOAD_URI_BEGIN[] =          "\",\"uri\":\"";
static char const PAYLOAD_METHOD_BEGIN[] =       "\",\"method\":\"";
static char const PAYLOAD_VERSION_BEGIN[] =      "\",\"version\":\"";
static char const PAYLOAD_END[] =                "\"}";
static int handler(struct mg_connection *c, void *cbdata) {
    struct mg_request_info const *const request_info = mg_get_request_info(c);
    char const *const method = request_info->request_method;
    size_t const method_len = strlen(method);
    char const *const uri_without_query = request_info->request_uri;
    size_t const uri_without_query_len = strlen(uri_without_query);
    char const *const version = request_info->http_version;
    size_t const version_len = strlen(version);
    char const *const query = request_info->query_string;
    size_t const query_len = query != NULL ? strlen(query) : 0;
    long long body_len = request_info->content_length;
    if (body_len == -1) {
        body_len = 0;
    }
    uint8_t *const body = malloc(body_len);
    if (mg_read(c, body, body_len) != body_len) {
        mg_send_http_error(c, 400, "", "Invalid request body!");
        free(body);
        return 400;
    }
    int const num_headers = request_info->num_headers;
    struct mg_header const *const headers = request_info->http_headers;

    char *buf = (char *)malloc(INITIAL_BUF_SIZE); // The buffer that contains the response.
    size_t buf_size = INITIAL_BUF_SIZE;           // Its size
    size_t buf_size_remaining = INITIAL_BUF_SIZE; // The amount of buf that's left
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_START, sizeof(PAYLOAD_START) - 1);

    for (int i = 0; i < num_headers; i++) {
        struct mg_header const curr = headers[i];
        if (i == 0) {
            add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_FIRST_HEADER_START, sizeof(PAYLOAD_FIRST_HEADER_START) - 1);
        } else {
            add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_HEADER_START, sizeof(PAYLOAD_HEADER_START) - 1);
        }

        char const *const name = headers[i].name;
        size_t name_len = strlen(name);
        char const *const value = headers[i].value;
        size_t value_len = strlen(value);

        // Name
        if (base64_encoded_len(name_len) + 1 > sizeof(B64_SCRATCH_SPACE)) { // + 1 because mg_base64_encode adds a null
            mg_send_http_error(c, 400, "", "Header name too long");
            free(body);
            free(buf);
            return 400;
        }
        mg_base64_encode(name, name_len, B64_SCRATCH_SPACE, &(size_t){sizeof(B64_SCRATCH_SPACE)});
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(name_len));
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_HEADER_MID, sizeof(PAYLOAD_HEADER_MID) - 1);

        // Value
        if (base64_encoded_len(value_len) + 1 > sizeof(B64_SCRATCH_SPACE)) { // + 1 because mg_base64_encode adds a null
            mg_send_http_error(c, 400, "", "Header value too long");
            free(body);
            free(buf);
            return 400;
        }
        mg_base64_encode(value, value_len, B64_SCRATCH_SPACE, &(size_t){sizeof(B64_SCRATCH_SPACE)});
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(value_len));
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_HEADER_END, sizeof(PAYLOAD_HEADER_END) - 1);
    }

    // Body
    if (base64_encoded_len(body_len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_send_http_error(c, 400, "", "Request body too large");
        free(body);
        free(buf);
        return 400;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_BODY_BEGIN, sizeof(PAYLOAD_BODY_BEGIN) - 1);
    mg_base64_encode(body, body_len, B64_SCRATCH_SPACE, &(size_t){sizeof(B64_SCRATCH_SPACE)});
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(body_len));

    // URI
    if (uri_without_query_len + 1 + query_len + 1 > sizeof(STRCAT_SCRATCH_SPACE)) {
        mg_send_http_error(c, 400, "", "Request URI too long");
        free(body);
        free(buf);
        return 400;
    }
    size_t uri_len = 0;
    STRCAT_SCRATCH_SPACE[uri_len] = '\0';
    if (uri_without_query_len > 0) {
        memcpy(STRCAT_SCRATCH_SPACE, uri_without_query, uri_without_query_len);
        uri_len += uri_without_query_len;
        STRCAT_SCRATCH_SPACE[uri_len] = '\0';
    }
    if (query_len > 0) {
        STRCAT_SCRATCH_SPACE[uri_len] = '?';
        uri_len++;
        memcpy(STRCAT_SCRATCH_SPACE + uri_len, query, query_len);
        uri_len += query_len;
        STRCAT_SCRATCH_SPACE[uri_len] = '\0';
    }
    if (base64_encoded_len(uri_len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_send_http_error(c, 400, "", "Request URI too long");
        free(body);
        free(buf);
        return 400;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_URI_BEGIN, sizeof(PAYLOAD_URI_BEGIN) - 1);
    mg_base64_encode(STRCAT_SCRATCH_SPACE, uri_len, B64_SCRATCH_SPACE, &(size_t){sizeof(B64_SCRATCH_SPACE)});
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(uri_len));

    // Method
    if (base64_encoded_len(method_len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_send_http_error(c, 400, "", "Request method too long");
        free(body);
        free(buf);
        return 400;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_METHOD_BEGIN, sizeof(PAYLOAD_METHOD_BEGIN) - 1);
    mg_base64_encode(method, method_len, B64_SCRATCH_SPACE, &(size_t){sizeof(B64_SCRATCH_SPACE)});
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(method_len));

    // Version
    if (base64_encoded_len(method_len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_send_http_error(c, 400, "", "Request method too long");
        free(body);
        free(buf);
        return 400;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_VERSION_BEGIN, sizeof(PAYLOAD_VERSION_BEGIN) - 1);
    mg_base64_encode(version, version_len, B64_SCRATCH_SPACE, &(size_t){sizeof(B64_SCRATCH_SPACE)});
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(version_len));

    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_END, sizeof(PAYLOAD_END));

    mg_send_http_ok(c, "Content-Type: application/json", strlen(buf));
    mg_write(c, buf, strlen(buf));
    free(body);
    free(buf);
    return 200;
}

static int log_message(struct mg_connection const *, char const *const message) {
    puts(message);
    return 1;
}

int main(void) {
    char const *options[] = {
        "listening_ports",
        "80",
        "request_timeout_ms",
        "10000",
        "error_log_file",
        "error.log",
        0
    };

    mg_init_library(0);

    struct mg_callbacks callbacks = {0};
    callbacks.log_message = log_message;

    struct mg_context *const ctx = mg_start(&callbacks, 0, options);
    if (ctx == NULL) {
        fputs("mg_start failed!", stderr);
        return EXIT_FAILURE;
    }

    mg_set_request_handler(ctx, "/*", handler, 0);

    while (1) {
        sleep(1);
    }
}
