// Copyright (c) 2020 Cesanta Software Limited
// All rights reserved
// Heavily modified by Ben Kallus.

#include <stdio.h>
#include "mongoose.h"

static int const s_debug_level = MG_LL_INFO;
static char const s_listening_address[] = "http://0.0.0.0:80";

// Handle interrupts, like Ctrl-C
static int s_signo;
static void signal_handler(int signo) {
    s_signo = signo;
}

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
void add_to_buffer(char **const buf_ptr, size_t *const buf_size_ptr, size_t *const buf_size_remaining_ptr, char const *const src, size_t const src_size) {
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
static void cb(struct mg_connection *c, int ev, void *ev_data) {
    if (ev != MG_EV_HTTP_MSG) {
        return;
    }
    struct mg_http_message parsed_request = {0};
    parsed_request = *(struct mg_http_message *)ev_data;
    // mg_http_parse((char *)c->recv.buf, c->recv.len, &parsed_request);

    char *buf = (char *)malloc(INITIAL_BUF_SIZE); // The buffer that contains the request.
    size_t buf_size = INITIAL_BUF_SIZE;           // Its size
    size_t buf_size_remaining = INITIAL_BUF_SIZE; // The amount of buf that's left
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_START, sizeof(PAYLOAD_START) - 1);

    int headers_encountered = 0;
    for (int i = 0; i < MG_MAX_HTTP_HEADERS; i++) {
        if (parsed_request.headers[i].name.buf == NULL && parsed_request.headers[i].value.buf == NULL) { // Empty header
            continue;
        }
        struct mg_http_header const curr = parsed_request.headers[i];
        if (headers_encountered == 0) {
            add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_FIRST_HEADER_START, sizeof(PAYLOAD_FIRST_HEADER_START) - 1);
        } else {
            add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_HEADER_START, sizeof(PAYLOAD_HEADER_START) - 1);
        }

        // Name
        if (base64_encoded_len(curr.name.len) + 1 > sizeof(B64_SCRATCH_SPACE)) { // + 1 because mg_base64_encode adds a null
            mg_http_reply(c, 400, "", "Header name too long");
            free(buf);
            return;
        }
        mg_base64_encode((unsigned char *)curr.name.buf, curr.name.len, B64_SCRATCH_SPACE, sizeof(B64_SCRATCH_SPACE));
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(curr.name.len));
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_HEADER_MID, sizeof(PAYLOAD_HEADER_MID) - 1);

        // Value
        if (base64_encoded_len(curr.value.len) + 1 > sizeof(B64_SCRATCH_SPACE)) { // + 1 because mg_base64_encode adds a null
            mg_http_reply(c, 400, "", "Header value too long");
            free(buf);
            return;
        }
        mg_base64_encode((unsigned char *)curr.value.buf, curr.value.len, B64_SCRATCH_SPACE, sizeof(B64_SCRATCH_SPACE));
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(curr.value.len));
        add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_HEADER_END, sizeof(PAYLOAD_HEADER_END) - 1);
        headers_encountered++;
    }

    // Body
    if (base64_encoded_len(parsed_request.body.len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_http_reply(c, 400, "", "Request body too large");
        free(buf);
        return;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_BODY_BEGIN, sizeof(PAYLOAD_BODY_BEGIN) - 1);
    mg_base64_encode((unsigned char *)parsed_request.body.buf, parsed_request.body.len, B64_SCRATCH_SPACE, sizeof(B64_SCRATCH_SPACE));
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(parsed_request.body.len));

    // URI
    if (parsed_request.uri.len + 1 + parsed_request.query.len + 1 > sizeof(STRCAT_SCRATCH_SPACE)) {
        mg_http_reply(c, 400, "", "Request URI too long");
        free(buf);
        return;
    }
    size_t uri_len = 0;
    STRCAT_SCRATCH_SPACE[uri_len] = '\0';
    if (parsed_request.uri.len > 0) {
        memcpy(STRCAT_SCRATCH_SPACE, parsed_request.uri.buf, parsed_request.uri.len);
        uri_len += parsed_request.uri.len;
        STRCAT_SCRATCH_SPACE[uri_len] = '\0';
    }
    if (parsed_request.query.len > 0) {
        STRCAT_SCRATCH_SPACE[uri_len] = '?';
        uri_len++;
        memcpy(STRCAT_SCRATCH_SPACE + uri_len, parsed_request.query.buf, parsed_request.query.len);
        uri_len += parsed_request.query.len;
        STRCAT_SCRATCH_SPACE[uri_len] = '\0';
    }
    if (base64_encoded_len(uri_len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_http_reply(c, 400, "", "Request URI too long");
        free(buf);
        return;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_URI_BEGIN, sizeof(PAYLOAD_URI_BEGIN) - 1);
    mg_base64_encode((unsigned char *)STRCAT_SCRATCH_SPACE, uri_len, B64_SCRATCH_SPACE, sizeof(B64_SCRATCH_SPACE));
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(uri_len));

    // Method
    if (base64_encoded_len(parsed_request.method.len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_http_reply(c, 400, "", "Request method too long");
        free(buf);
        return;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_METHOD_BEGIN, sizeof(PAYLOAD_METHOD_BEGIN) - 1);
    mg_base64_encode((unsigned char *)parsed_request.method.buf, parsed_request.method.len, B64_SCRATCH_SPACE, sizeof(B64_SCRATCH_SPACE));
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(parsed_request.method.len));

    // Version
    if (base64_encoded_len(parsed_request.method.len) + 1 > sizeof(B64_SCRATCH_SPACE)) {
        mg_http_reply(c, 400, "", "Request method too long");
        free(buf);
        return;
    }
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_VERSION_BEGIN, sizeof(PAYLOAD_VERSION_BEGIN) - 1);
    mg_base64_encode((unsigned char *)parsed_request.proto.buf, parsed_request.proto.len, B64_SCRATCH_SPACE, sizeof(B64_SCRATCH_SPACE));
    add_to_buffer(&buf, &buf_size, &buf_size_remaining, B64_SCRATCH_SPACE, base64_encoded_len(parsed_request.proto.len));

    add_to_buffer(&buf, &buf_size, &buf_size_remaining, PAYLOAD_END, sizeof(PAYLOAD_END));

    mg_http_reply(c, 200, "Content-Type: application/json\r\n", "%s", buf);
    free(buf);
}

int main(void) {
    // Initialise stuff
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    mg_log_set(s_debug_level);

    struct mg_mgr mgr;
    mg_mgr_init(&mgr);

    struct mg_connection *c = mg_http_listen(&mgr, s_listening_address, cb, NULL);
    if (c == NULL) {
        MG_ERROR(("Cannot listen on %s. Use http://ADDR:PORT or :PORT", s_listening_address));
        exit(EXIT_FAILURE);
    }

    // Start infinite event loop
    MG_INFO(("Mongoose version : v%s", MG_VERSION));
    MG_INFO(("Listening on     : %s", s_listening_address));
    while (s_signo == 0) {
        mg_mgr_poll(&mgr, 1000);
    }
    mg_mgr_free(&mgr);
    MG_INFO(("Exiting on signal %d", s_signo));
    return 0;
}
