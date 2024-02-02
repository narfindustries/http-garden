#include <signal.h>

#include <libsoup/soup.h>
#include <glib/gstdio.h>
#include <glib/gbase64.h>

static void cb(SoupServer *server, SoupServerMessage *msg, char const *path, GHashTable *query, gpointer) {
    GString *result = g_string_new("");

    gchar *b64_method = g_base64_encode(soup_server_message_get_method(msg), strlen(soup_server_message_get_method(msg)));
    char const *b64_version;
    if (soup_server_message_get_http_version(msg) == 0) {
        b64_version = "MS4w";
    } else {
        b64_version = "MS4x";
    }

    gchar *b64_uri = g_base64_encode(path, strlen(path)); // This is missing the query, but it's ok for now

    g_string_append_printf(result, "{\"method\":\"%s\",\"version\":\"%s\",\"uri\":\"%s\",\"headers\":[", b64_method,  b64_version, b64_uri);
    g_free(b64_method);
    g_free(b64_uri);

    int first = 1;
    char const *name;
    char const *value;
    SoupMessageHeadersIter iter;
    soup_message_headers_iter_init(&iter, soup_server_message_get_request_headers(msg));
    while (soup_message_headers_iter_next(&iter, &name, &value)) {
        if (!first) {
            g_string_append_printf(result, "%s", ",");
        }
        first = 0;
        gchar *b64_name = g_base64_encode(name, strlen(name));
        gchar *b64_value = g_base64_encode(value, strlen(value));
        g_string_append_printf(result, "[\"%s\", \"%s\"]", b64_name, b64_value);
        g_free(b64_name);
        g_free(b64_value);
    }
    g_string_append_printf(result, "%s", "],");

    SoupMessageBody *body = soup_server_message_get_request_body(msg);
    gchar *b64_body = g_base64_encode(body->data, body->length);
    g_string_append_printf(result, "\"body\":\"%s\"}", b64_body);

    soup_server_message_set_response(msg, "application/json", SOUP_MEMORY_COPY, result->str, result->len);
    soup_server_message_set_status(msg, SOUP_STATUS_OK, NULL);
    g_string_free(result, TRUE);
}

static void quit(int) {
    exit(0);
}

int main(void) {
    signal(SIGINT, quit);
    GError *error = NULL;

    SoupServer *server = soup_server_new(NULL, NULL);
    soup_server_listen_all(server, 80, 0, &error);
    soup_server_add_handler(server, NULL, cb, NULL, NULL);

    g_main_loop_run(g_main_loop_new(NULL, TRUE));
}
