#include <microhttpd.h>
#include <apr-1.0/apr_encode.h> // for APR_ENCODE_NONE, apr_encode_base64
#include <assert.h> // for assert
#include <stdio.h> // for dprintf
#include <string.h> // for strlen
#include <unistd.h> // for write, sleep, read, mkstemp, write
#include <stdlib.h> // for malloc, free

struct process_header_arg {
    int fd;
    int first;
};

struct str {
    char *data;
    size_t len;
};

// Base64-encodes some data.
// Note that result.data must be freed
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

static void base64_write(int const fd, char const * const data, size_t const len) {
    struct str b64_encoded_data = base64_encode(data, len);
    write(fd, b64_encoded_data.data, b64_encoded_data.len);
    free(b64_encoded_data.data);
}

static enum MHD_Result process_header(void *uncast_arg, enum MHD_ValueKind unused, char const *key, size_t key_size, char const *value, size_t value_size) {
    (void)unused;

    struct process_header_arg *arg = (struct process_header_arg *)uncast_arg;

    if (arg->first) {
        arg->first = 0;
    } else {
        dprintf(arg->fd, ",");
    }

    dprintf(arg->fd, "[\"");
    base64_write(arg->fd, key, key_size);
    dprintf(arg->fd, "\",\"");
    base64_write(arg->fd, value, value_size);
    dprintf(arg->fd, "\"]");

    return MHD_YES;
}

ssize_t const READ_SIZE = 4096;
static struct str read_fd(int const fd) {
    char *result = malloc(READ_SIZE);
    assert(result != NULL);

    ssize_t buffer_size = READ_SIZE;
    ssize_t total_bytes_read = 0;
    while (1) {
        ssize_t bytes_just_read = read(fd, result + total_bytes_read, READ_SIZE);
        assert(bytes_just_read != -1);

        total_bytes_read += bytes_just_read;
        if (bytes_just_read < READ_SIZE) {
            break;
        }

        buffer_size += READ_SIZE;
        result = realloc(result, buffer_size);
        assert(result != NULL);
    }

    return (struct str){
        .data = result,
        .len = total_bytes_read
    };
}

static enum MHD_Result callback(
    void *unused0, // custom arg
    struct MHD_Connection *connection, // The place where headers are read from
    char const *url, // URL
    char const *method, // method
    char const *version, // version
    char const *upload_data, // message body data
    size_t *upload_data_size, // in-out; set to zero when upload_data is processed
    void **unused1 // custom arg
) {
    (void)unused0;
    (void)unused1;

    static int first = 1;
    static int fd = -1;
    static int body_fd = -1;

    enum MHD_Result ret;

    if (first) {
        char template[] = {'g', 'a', 'r', 'd', 'e', 'n', '-', 'm', 'e', 's', 's', 'a', 'g', 'e', '-', 'X', 'X', 'X', 'X', 'X', 'X', '\0'};
        fd = mkstemp(template); // This never gets closed because it's too annoying to deal with the race condition.
        assert(fd != -1);

        char body_template[] = {'g', 'a', 'r', 'd', 'e', 'n', '-', 'b', 'o', 'd', 'y', '-', 'X', 'X', 'X', 'X', 'X', 'X', '\0'};
        body_fd = mkstemp(body_template);
        assert(body_fd != -1);

        dprintf(fd, "{\"method\":\"");
        base64_write(fd, method, strlen(method));
        dprintf(fd, "\",\"uri\":\"");
        base64_write(fd, url, strlen(url));
        dprintf(fd, "\",\"version\":\"");
        base64_write(fd, version, strlen(version));
        dprintf(fd, "\",\"headers\":[");

        struct process_header_arg arg = {
            .fd = fd,
            .first = 1
        };

        MHD_get_connection_values_n(connection, MHD_HEADER_KIND, process_header, &arg);

        dprintf(fd, "],\"body\":\"");

        first = 0;
        ret = MHD_YES;
    }
    else if (*upload_data_size != 0) { // Not the first call, and the data's not done being uploaded
        write(body_fd, upload_data, *upload_data_size);
        *upload_data_size = 0;
        ret = MHD_YES;
    }
    else { // Final call
        lseek(body_fd, 0, SEEK_SET);
        struct str body = read_fd(body_fd);
        base64_write(fd, body.data, body.len);
        free(body.data);
        dprintf(fd, "\"}");
        close(body_fd);
        body_fd = -1;

        off_t const json_len = lseek(fd, 0, SEEK_CUR);
        lseek(fd, 0, SEEK_SET); // Reset the pointer
        struct MHD_Response *const response = MHD_create_response_from_fd(json_len, fd);
        ret = MHD_queue_response(connection, MHD_HTTP_OK, response);

        MHD_destroy_response(response);

        first = 1;
        fd = -1;

        *upload_data_size = 0;
    }

    return ret;
}

int main(void) {
    if (
        MHD_start_daemon(
            MHD_USE_AUTO | MHD_USE_INTERNAL_POLLING_THREAD | MHD_USE_ERROR_LOG, // flags
            80, // port
            NULL, // auth callback
            NULL, // auth callback custom arg
            &callback, // handler
            NULL, // handler custom arg
            MHD_OPTION_END // no options
        ) != NULL
    ) {
        while (1) {
            sleep(1);
        }
    }
}
