vcl 4.1;

backend default {
    .host = "PROXY_BACKEND_PLACEHOLDER";
    .port = "80";
}

sub vcl_recv {
    return(pass);
}
