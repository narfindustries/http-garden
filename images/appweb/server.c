#include <stdlib.h> // for EXIT_FAILURE
#include <apr-1.0/apr_encode.h> // for for APR_ENCODE_NONE, apr_encode_base64

#include "appweb.h"

struct str {
    char *data;
    size_t len;
};

static struct str base64_encode(char const *const data, size_t const len) {

    size_t result_len;
    apr_encode_base64(NULL, data, len, APR_ENCODE_NONE, &result_len);

    char *result = malloc(result_len);
    assert(result != NULL);

    apr_encode_base64(result, data, len, APR_ENCODE_NONE, NULL);

    return (struct str){
        .data = result,
        .len = result_len - 1 // For the NUL
    };
}

char *base64_encode_c_str(char const *const data) {
    return base64_encode(data, strlen(data)).data;
}

static void handle_ready_queue(struct HttpQueue *q) {
    struct HttpStream *stream = q->stream;
    if (stream == NULL) {
        exit(EXIT_FAILURE);
    }

    struct HttpRx *req = stream->rx;
    if (req == NULL) {
        exit(EXIT_FAILURE);
    }

    httpSetStatus(stream, 200);
    char *b64_method = base64_encode_c_str(req->method);
    char *b64_uri = base64_encode_c_str(req->uri);
    httpWrite(q, "{\"method\":\"%s\",\"uri\":\"%s\",\"headers\":[", b64_method, b64_uri);
    free(b64_method);
    free(b64_uri);

    bool first = 1;
    struct MprKey *key;
    void *val;
    for (ITERATE_KEY_DATA(req->headers, key, val)) {
        char *b64_key = base64_encode_c_str(key->key);
        char *b64_val = base64_encode_c_str((char *)val);
        httpWrite(q, "%s[\"%s\",\"%s\"]", first ? "" : ",", b64_key, b64_val);
        free(b64_val);
        free(b64_key);
        if (first) {
            first = 0;
        }
    }

    size_t capacity = 0;
    char *body = malloc(capacity);
    if (body == NULL) {
        exit(EXIT_FAILURE);
    }
    while (1) {
        #define READ_SIZE (65536)
        char chunk[READ_SIZE];
        #undef READ_SIZE
        ssize bytes_read = httpRead(stream, chunk, sizeof chunk);
        if (bytes_read <= 0) {
            break;
        } else {
            size_t const new_capacity = capacity + bytes_read;
            body = realloc(body, new_capacity);
            if (body == NULL) {
                exit(EXIT_FAILURE);
            }
            memcpy(body + capacity, chunk, bytes_read);
            capacity = new_capacity;
        }
    }
    struct str b64_body = base64_encode(body, capacity);
    free(body);

    char *b64_version = base64_encode_c_str(req->protocol);

    httpWrite(q, "],\"body\":\"%.*s\",\"version\":\"%s\"}", (int)b64_body.len, b64_body.data, b64_version);
    free(b64_body.data);
    free(b64_version);

    httpFinalize(stream);
}

int httpEchoHandlerInit(struct Http *http, struct MprModule *module) {
    struct HttpStage *stage = httpCreateHandler("echoHandler", module);

    if (stage == NULL) {
        return MPR_ERR_CANT_CREATE;
    }
    stage->ready = handle_ready_queue;

    return 0;
}
