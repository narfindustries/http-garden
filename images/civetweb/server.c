#include <unistd.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "civetweb.h"

static int ExampleHandler(struct mg_connection *conn, void *_) {
	return 200;
}

static int log_message(const struct mg_connection *conn, const char *message) {
	puts(message);
	return 1;
}

int main(int argc, char *argv[]) {
	const char *options[] = {"listening_ports",
	                         80,
	                         "request_timeout_ms",
	                         "10000",
	                         "error_log_file",
	                         "error.log",
	                         0};

	mg_init_library(0);

	struct mg_callbacks callbacks = {0};
	callbacks.log_message = log_message;

	struct mg_context *ctx = mg_start(&callbacks, 0, options);
	if (ctx == NULL) {
		fprintf(stderr, "Cannot start CivetWeb - mg_start failed.\n");
		return EXIT_FAILURE;
	}

	mg_set_request_handler(ctx, "/*", handler, 0);

	while (1);
}
