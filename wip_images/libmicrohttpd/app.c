/*
     This file is part of libmicrohttpd
     Copyright (C) 2007 Christian Grothoff (and other contributing authors)
     Copyright (C) 2014-2022 Evgeny Grin (Karlson2k)

     This library is free software; you can redistribute it and/or
     modify it under the terms of the GNU Lesser General Public
     License as published by the Free Software Foundation; either
     version 2.1 of the License, or (at your option) any later version.

     This library is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     Lesser General Public License for more details.

     You should have received a copy of the GNU Lesser General Public
     License along with this library; if not, write to the Free Software
     Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
*/
/**
 * @file minimal_example.c
 * @brief minimal example for how to use libmicrohttpd
 * @author Christian Grothoff
 * @author Karlson2k (Evgeny Grin)
 * @author Ben Kallus
 */

#include <microhttpd.h>
#include <stdio.h> // For printf, puts
#include <stddef.h> // For NULL

static enum MHD_Result handler(void *, struct MHD_Connection *connection, const char *url, const char *method, const char *version, const char *upload_data, size_t *upload_data_size, void **req_cls) {
    static int aptr;

    if (&aptr != *req_cls) {
        /* do never respond on first call */
        *req_cls = &aptr;
        return MHD_YES;
    }
    *req_cls = NULL;                  /* reset when done */

    printf("URL: %s\n", url);
    printf("Method: %s\n", method);
    printf("Version: %s\n", version);
    if (upload_data_size != NULL && upload_data != NULL && *upload_data_size > 0) {
        printf("Upload data size: %zu\n", *upload_data_size);
        printf("Upload data: %.*s\n", *upload_data_size, upload_data);
        *upload_data_size = 0;
    }

    struct MHD_Response *const response = MHD_create_response_from_buffer_static(0, "");
    enum MHD_Result ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    printf("Return code: %d\n", ret);
    return MHD_YES;
}


int main (void) {
    if (
        MHD_start_daemon(
            MHD_USE_AUTO | MHD_USE_INTERNAL_POLLING_THREAD | MHD_USE_ERROR_LOG, // flags
            80, // port
            NULL, // Access control callback
            NULL, // Extra args to access control callback
            &handler, // Request handler callback
            NULL, // Extra argument to request handler callback
            MHD_OPTION_END
        ) == NULL) {
        return 1;
    }

    while (1);
}
