#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <apr-1.0/apr_encode.h>

#include <aws/common/allocator.h>
#include <aws/http/http.h>
#include <aws/http/request_response.h>
#include <aws/http/server.h>
#include <aws/io/channel_bootstrap.h>
#include <aws/io/event_loop.h>
#include <aws/io/socket.h>
#include <aws/io/stream.h>

struct parse_state {
    bool started;
    bool started_headers;
    struct aws_byte_cursor response_body;
    struct aws_byte_cursor request_body;
    struct aws_http_message *response;
};

static void byte_cursor_append(struct aws_byte_cursor *dst,
                               struct aws_byte_cursor src) {
    if (src.len == 0) {
        return;
    }
    uint8_t *new_buf = realloc(dst->ptr, dst->len + src.len);
    if (new_buf == NULL) {
        exit(EXIT_FAILURE);
    }
    dst->ptr = new_buf;
    memcpy(dst->ptr + dst->len, src.ptr, src.len);
    dst->len = dst->len + src.len;
}

static struct aws_byte_cursor base64_encode_cursor(struct aws_byte_cursor cursor) {
    struct aws_byte_cursor result;

    apr_encode_base64(NULL, (char *)cursor.ptr, cursor.len, APR_ENCODE_NONE, &result.len);

    result.ptr = malloc(result.len);
    if (result.ptr == NULL) {
        exit(EXIT_FAILURE);
    }

    result.len--;

    apr_encode_base64((char *)result.ptr, (char *)cursor.ptr, cursor.len, APR_ENCODE_NONE, NULL);

    return result;
}

static struct parse_state *parse_state_new(void) {
    struct parse_state *result = malloc(sizeof(struct parse_state));
    result->started = false;
    result->started_headers = false;
    if (result == NULL) {
        exit(EXIT_FAILURE);
    }
    result->response_body.ptr = malloc(0);
    if (result->response_body.ptr == NULL) {
        exit(EXIT_FAILURE);
    }
    result->response_body.len = 0;

    result->request_body.ptr = malloc(0);
    if (result->request_body.ptr == NULL) {
        exit(EXIT_FAILURE);
    }
    result->request_body.len = 0;

    result->response = aws_http_message_new_response(aws_default_allocator());
    if (result->response == NULL) {
        exit(EXIT_FAILURE);
    }

    return result;
}

static void parse_state_destroy(struct parse_state *parse_state) {
    aws_http_message_release(parse_state->response);
    free(parse_state->request_body.ptr);
    free(parse_state->response_body.ptr);
    free(parse_state);
}

static int on_request_headers(struct aws_http_stream *stream,
                              enum aws_http_header_block header_block,
                              const struct aws_http_header *header_array,
                              size_t num_headers, void *user_data) {
    if (header_block != AWS_HTTP_HEADER_BLOCK_MAIN) {
        // Trailers
        // or informational (which should never happen)
        return AWS_OP_SUCCESS;
    }

    struct parse_state *parse_state = user_data;
    if (!parse_state->started) {
        byte_cursor_append(&parse_state->response_body,
                           aws_byte_cursor_from_c_str("{\"method\":\""));

        struct aws_byte_cursor method_cursor;
        aws_http_stream_get_incoming_request_method(stream, &method_cursor);
        struct aws_byte_cursor b64_method_cursor = base64_encode_cursor(method_cursor);
        byte_cursor_append(&parse_state->response_body, b64_method_cursor);
        free(b64_method_cursor.ptr);

        byte_cursor_append(&parse_state->response_body,
                           aws_byte_cursor_from_c_str("\",\"uri\":\""));

        struct aws_byte_cursor uri_cursor;
        aws_http_stream_get_incoming_request_uri(stream, &uri_cursor);
        struct aws_byte_cursor b64_uri_cursor = base64_encode_cursor(uri_cursor);
        byte_cursor_append(&parse_state->response_body, b64_uri_cursor);
        free(b64_uri_cursor.ptr);

        byte_cursor_append(&parse_state->response_body, aws_byte_cursor_from_c_str("\",\"version\":\""));
        switch (aws_http_message_get_protocol_version(parse_state->response)) {
            case AWS_HTTP_VERSION_UNKNOWN:
                byte_cursor_append(&parse_state->response_body, aws_byte_cursor_from_c_str("VU5LTk9XTg=="));
                break;
            case AWS_HTTP_VERSION_1_0:
                byte_cursor_append(&parse_state->response_body, aws_byte_cursor_from_c_str("SFRUUC8xLjA="));
                break;
            case AWS_HTTP_VERSION_1_1:
                byte_cursor_append(&parse_state->response_body, aws_byte_cursor_from_c_str("SFRUUC8xLjE="));
                break;
            case AWS_HTTP_VERSION_2:
                byte_cursor_append(&parse_state->response_body, aws_byte_cursor_from_c_str("SFRUUC8y"));
                break;
            default:
                exit(EXIT_FAILURE);
                break;
        }

        byte_cursor_append(&parse_state->response_body,
                           aws_byte_cursor_from_c_str("\",\"headers\":["));

        parse_state->started = true;
    }

    for (size_t i = 0; i < num_headers; i++) {
        if (parse_state->started_headers) {
            byte_cursor_append(&parse_state->response_body,
                               aws_byte_cursor_from_c_str(","));
        } else {
            parse_state->started_headers = true;
        }
        byte_cursor_append(&parse_state->response_body,
                           aws_byte_cursor_from_c_str("[\""));
        struct aws_byte_cursor b64_header_name = base64_encode_cursor(header_array[i].name);
        byte_cursor_append(&parse_state->response_body, b64_header_name);
        free(b64_header_name.ptr);
        byte_cursor_append(&parse_state->response_body,
                           aws_byte_cursor_from_c_str("\",\""));

        struct aws_byte_cursor b64_header_value = base64_encode_cursor(header_array[i].value);
        byte_cursor_append(&parse_state->response_body, b64_header_value);
        free(b64_header_value.ptr);
        byte_cursor_append(&parse_state->response_body,
                           aws_byte_cursor_from_c_str("\"]"));
    }

    return AWS_OP_SUCCESS;
}

static int on_request_header_block_done(struct aws_http_stream *stream,
                                        enum aws_http_header_block header_block,
                                        void *user_data) {
    struct parse_state *parse_state = user_data;

    byte_cursor_append(&parse_state->response_body,
                       aws_byte_cursor_from_c_str("],\"body\":\""));

    return AWS_OP_SUCCESS;
}

static int on_request_body(struct aws_http_stream *stream,
                           const struct aws_byte_cursor *data,
                           void *user_data) {
    struct parse_state *parse_state = user_data;
    byte_cursor_append(&parse_state->request_body, *data);

    return AWS_OP_SUCCESS;
}

static void on_destroy(void *user_data) {
}

static void on_complete(struct aws_http_stream *stream, int error_code,
                       void *user_data) {
    struct parse_state *parse_state = user_data;
    parse_state_destroy(parse_state);
    aws_http_stream_release(stream);
}

static char *itoa(uint64_t n) {
    static char const UINT64_MAX_STR_DEC[] = "18446744073709551615";
    static char result[sizeof(UINT64_MAX_STR_DEC)];
    memset(result, 0, sizeof(result));

    if (n == 0) {
        result[0] = '0';
        return result;
    }

    for (int i = 0; n > 0; i++) {
        result[i] = '0' + n % 10;
        n /= 10;
    }

    for (uint64_t i = 0; i < strlen(result) / 2; i++) {
        char tmp = result[i];
        result[i] = result[strlen(result) - i - 1];
        result[strlen(result) - i - 1] = tmp;
    }

    return result;
}

static int on_request_done(struct aws_http_stream *stream, void *user_data) {
    struct parse_state *parse_state = user_data;
    struct aws_byte_cursor b64_request_body = base64_encode_cursor(parse_state->request_body);
    byte_cursor_append(&parse_state->response_body, b64_request_body);
    free(b64_request_body.ptr);

    byte_cursor_append(&parse_state->response_body, aws_byte_cursor_from_c_str("\"}"));

    if (aws_http_message_set_response_status(parse_state->response, 200) != AWS_OP_SUCCESS) {
        exit(EXIT_FAILURE);
    }

    struct aws_input_stream *istream = aws_input_stream_new_from_cursor(aws_default_allocator(), &parse_state->response_body);
    if (istream == NULL) {
        exit(EXIT_FAILURE);
    }

    struct aws_http_header headers[] = {
        {
            .name = aws_byte_cursor_from_c_str("Content-Length"),
            .value = aws_byte_cursor_from_c_str(itoa(parse_state->response_body.len))
        }
    };

    aws_http_message_add_header_array(parse_state->response, headers, sizeof(headers) / sizeof(headers[0]));
    aws_http_message_set_body_stream(parse_state->response, istream);
    aws_http_stream_send_response(stream, parse_state->response);

    return AWS_OP_SUCCESS;
}

static struct aws_http_stream *
on_incoming_request(struct aws_http_connection *connection, void *) {
    struct aws_http_request_handler_options options =
        AWS_HTTP_REQUEST_HANDLER_OPTIONS_INIT;
    options.server_connection = connection;
    options.on_request_headers = on_request_headers;
    options.on_request_header_block_done = on_request_header_block_done;
    options.on_request_body = on_request_body;
    options.on_request_done = on_request_done;
    options.on_complete = on_complete;
    options.on_destroy = on_destroy;
    options.user_data = parse_state_new();
    return aws_http_stream_new_server_request_handler(&options);
}

static void on_incoming_connection(struct aws_http_server *server,
                                   struct aws_http_connection *connection,
                                   int error_code, void *) {
    if (error_code) {
        return;
    }

    struct aws_http_server_connection_options options =
        AWS_HTTP_SERVER_CONNECTION_OPTIONS_INIT;
    options.on_incoming_request = on_incoming_request;

    aws_http_connection_configure_server(connection, &options);
}

int main(void) {
    aws_http_library_init(aws_default_allocator());

    struct aws_event_loop_group_options el_group_options = {
        1,                              // loop_count
        AWS_EVENT_LOOP_PLATFORM_DEFAULT // type
    };
    struct aws_event_loop_group *el_group =
        aws_event_loop_group_new(aws_default_allocator(), &el_group_options);
    if (el_group == NULL) {
        return EXIT_FAILURE;
    }

    struct aws_server_bootstrap *server_bootstrap =
        aws_server_bootstrap_new(aws_default_allocator(), el_group);
    if (server_bootstrap == NULL) {
        return EXIT_FAILURE;
    }

    struct aws_socket_endpoint socket_endpoint = {"0.0.0.0", 80};
    struct aws_socket_options socket_options = {
        AWS_SOCKET_STREAM,                // type
        AWS_SOCKET_IPV4,                  // domain
        AWS_SOCKET_IMPL_PLATFORM_DEFAULT, // impl_type
        1000,                             // connect_timeout_ms
        0,    // keep_alive_interval_sec (gets defaulted)
        0,    // keep_alive_timeout_sec (gets defaulted)
        0,    // keep_alive_max_failed_probes (gets defaulted)
        true, // keepalive
        {0},  // network_interface_name (optional)
    };

    struct aws_http_server_options http_server_options =
        AWS_HTTP_SERVER_OPTIONS_INIT;
    http_server_options.allocator = aws_default_allocator();
    http_server_options.bootstrap = server_bootstrap;
    http_server_options.endpoint = &socket_endpoint;
    http_server_options.socket_options = &socket_options;
    http_server_options.on_incoming_connection = on_incoming_connection;

    struct aws_http_server *http_server =
        aws_http_server_new(&http_server_options);
    if (http_server == NULL) {
        return EXIT_FAILURE;
    }

    while (1) {
        sleep(UINT_MAX);
    }
}
