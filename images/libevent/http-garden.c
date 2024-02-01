/*
  Modified from libevent/sample/http-server.c by Ben Kallus.
 */

/* Compatibility for possible missing IPv6 declarations */
#include "../util-internal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/types.h>
#include <sys/stat.h>

#include <sys/stat.h>
#include <sys/socket.h>
#include <assert.h>
#include <fcntl.h>
#include <unistd.h>
#include <dirent.h>
#include <signal.h>

#include <event2/event.h>
#include <event2/http.h>
#include <event2/http_struct.h>
#include <event2/listener.h>
#include <event2/buffer.h>
#include <event2/util.h>
#include <event2/keyvalq_struct.h>

#include <netinet/in.h>
#include <arpa/inet.h>


// Copied from ../ws.c
static const char basis_64[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static int
Base64encode(char *encoded, const char *string, int len)
{
    int i;
    char *p;

    p = encoded;
    for (i = 0; i < len - 2; i += 3) {
        *p++ = basis_64[(string[i] >> 2) & 0x3F];
        *p++ = basis_64[((string[i] & 0x3) << 4) |
                        ((int)(string[i + 1] & 0xF0) >> 4)];
        *p++ = basis_64[((string[i + 1] & 0xF) << 2) |
                        ((int)(string[i + 2] & 0xC0) >> 6)];
        *p++ = basis_64[string[i + 2] & 0x3F];
    }
    if (i < len) {
        *p++ = basis_64[(string[i] >> 2) & 0x3F];
        if (i == (len - 1)) {
            *p++ = basis_64[((string[i] & 0x3) << 4)];
            *p++ = '=';
        } else {
            *p++ = basis_64[((string[i] & 0x3) << 4) |
                            ((int)(string[i + 1] & 0xF0) >> 4)];
            *p++ = basis_64[((string[i + 1] & 0xF) << 2)];
        }
        *p++ = '=';
    }

    *p++ = '\0';
    return p - encoded;
}

static void
dump_request_cb(struct evhttp_request *req, void *arg)
{
    (void)arg;
    char template[] = {'g', 'a', 'r', 'd', 'e', 'n', '-', 'm', 'e', 's', 's', 'a', 'g', 'e', '-', 'X', 'X', 'X', 'X', 'X', 'X', '\0'};
    int const fd = mkstemp(template);
    assert(fd != -1);
    const char *method;
    switch (evhttp_request_get_command(req)) {
    case EVHTTP_REQ_GET:
        method = "R0VU";
        break;
    case EVHTTP_REQ_POST:
        method = "UE9TVA==";
        break;
    case EVHTTP_REQ_HEAD:
        method = "SEVBRA==";
        break;
    case EVHTTP_REQ_PUT:
        method = "UFVU";
        break;
    case EVHTTP_REQ_DELETE:
        method = "REVMRVRF";
        break;
    case EVHTTP_REQ_OPTIONS:
        method = "T1BUSU9OUw==";
        break;
    case EVHTTP_REQ_TRACE:
        method = "VFJBQ0U=";
        break;
    case EVHTTP_REQ_CONNECT:
        method = "Q09OTkVDVA==";
        break;
    case EVHTTP_REQ_PATCH:
        method = "UEFUQ0g=";
        break;
    case EVHTTP_REQ_PROPFIND:
        method = "UFJPUEZJTkQ=";
        break;
    case EVHTTP_REQ_PROPPATCH:
        method = "UFJPUFBBVENI";
        break;
    case EVHTTP_REQ_MKCOL:
        method = "TUtDT0w=";
        break;
    case EVHTTP_REQ_LOCK:
        method = "TE9DSw==";
        break;
    case EVHTTP_REQ_UNLOCK:
        method = "VU5MT0NL";
        break;
    case EVHTTP_REQ_COPY:
        method = "Q09QWQ==";
        break;
    case EVHTTP_REQ_MOVE:
        method = "TU9WRQ==";
        break;
    default:
        assert(0); // This should never happen
    }

    dprintf(fd, "{\"method\":\"%s\",\"headers\":[", method);

    struct evkeyvalq *headers = evhttp_request_get_input_headers(req);
    int first = 1;
    for (struct evkeyval *header = headers->tqh_first; header; header = header->next.tqe_next) {
        size_t const key_len = strlen(header->key);
        // len(b64(s)) = ceil(len(s) / 3) * 4 (+1 for '\0')
        char *b64_key = calloc((key_len / 3 + 1) * 4 + 1, sizeof(char));
        assert(b64_key != NULL);
        Base64encode(b64_key, header->key, key_len);
        size_t const value_len = strlen(header->value);
        char *b64_value = calloc((value_len / 3 + 1) * 4 + 1, sizeof(char));
        assert(b64_value != NULL);
        Base64encode(b64_value, header->value, value_len);

        dprintf(fd, "%s[\"%s\",\"%s\"]", first ? "" : ",", b64_key, b64_value);

        free(b64_key);
        free(b64_value);
        first = 0;
    }

    dprintf(fd, "],\"body\":\"");
    struct evbuffer *buf = evhttp_request_get_input_buffer(req);
    while (evbuffer_get_length(buf)) {
        char cbuf[128];
        int n = evbuffer_remove(buf, cbuf, sizeof(cbuf));
        char b64_cbuf[173]; // ceil(128 / 3) * 4 (+1 for '\0')
        Base64encode(b64_cbuf, cbuf, n);
        dprintf(fd, "%s", b64_cbuf);
    }
    char version[] = {'0' + req->major, '.', '\0', '\0', '\0', '\0'};
    size_t version_len = 2;
    unsigned int const minor_as_uint = req->minor;
    if (minor_as_uint / 100) {
        version[version_len] = '0' + minor_as_uint / 100;
        version_len++;
    }
    if (minor_as_uint / 10) {
        version[version_len] = '0' + (minor_as_uint / 10) % 10;
        version_len++;
    }
    version[version_len] = '0' + minor_as_uint % 10;
    version_len++;
    char b64_version[17] = {0}; // len(b64encode(b"HTTP/1.255")) == 16 (+1 for '\0')
    Base64encode(b64_version, version, version_len);
    dprintf(fd, "\",\"version\":\"%s\",", b64_version);

    char const *const uri = evhttp_request_get_uri(req);
    size_t const uri_len = strlen(uri);
    char *const b64_uri = calloc((uri_len / 3 + 1) * 4 + 1, sizeof(char));
    Base64encode(b64_uri, uri, uri_len);
    dprintf(fd, "\"uri\":\"%s\"}", b64_uri);

    struct evbuffer *const outbuf = evbuffer_new();
    int const rc = evbuffer_add_file(outbuf, fd, 0, -1);
    assert(rc != -1);
    evhttp_send_reply(req, 200, "OK", outbuf);
}

static void
do_term(int sig, short events, void *arg)
{
    (void)events;
    (void)sig;
    event_base_loopbreak((struct event_base *)arg);
}

static void
display_listen_sock(struct evhttp_bound_socket *handle)
{
    evutil_socket_t fd = evhttp_bound_socket_get_fd(handle);
    struct sockaddr_storage ss = {0};
    ev_socklen_t socklen = sizeof(ss);
    assert(!getsockname(fd, (struct sockaddr *)&ss, &socklen));

    int got_port = ntohs(((struct sockaddr_in *)&ss)->sin_port);
    void *inaddr = &((struct sockaddr_in *)&ss)->sin_addr;

    char addrbuf[128];
    char const *addr = evutil_inet_ntop(ss.ss_family, inaddr, addrbuf, sizeof(addrbuf));
    assert(addr != NULL);
    printf("Listening on %s:%d\n", addr, got_port);
}

int main(void)
{
    struct event_config *cfg = event_config_new();
    assert(cfg != NULL);

    struct event_base *base = event_base_new_with_config(cfg);
    assert(base != NULL);
    event_config_free(cfg);

    /* Create a new evhttp object to handle requests. */
    struct evhttp *http = evhttp_new(base);
    assert(http != NULL);

    /* We want to accept arbitrary requests, so we need to set a "generic"
     * cb.  We can also add callbacks for specific paths. */
    evhttp_set_gencb(http, dump_request_cb, NULL);

    struct evhttp_bound_socket *handle = evhttp_bind_socket_with_handle(http, "0.0.0.0", 80);
    assert(handle != NULL);

    display_listen_sock(handle);

    struct event *term = evsignal_new(base, SIGINT, do_term, base);
    assert(term);
    assert(!event_add(term, NULL));

    event_base_dispatch(base);

    evhttp_free(http);
    event_free(term);
    event_base_free(base);
}
