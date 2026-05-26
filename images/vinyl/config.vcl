vcl 4.1;

backend default {
    .host = "BACKEND_HOST_PLACEHOLDER";
    .port = "BACKEND_PORT_PLACEHOLDER";
}

sub vcl_recv {
    return(pass);
}
