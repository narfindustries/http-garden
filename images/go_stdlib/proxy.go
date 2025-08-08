package main

import (
	"net/http"
	"net/http/httputil"
	"net/url"
)

func main() {
	url, _ := url.Parse("http://BACKEND_HOST_PLACEHOLDER:BACKEND_PORT_PLACEHOLDER")
	proxy := httputil.NewSingleHostReverseProxy(url)
	http.HandleFunc("/", proxy.ServeHTTP)
	http.ListenAndServe(":80", nil)
}
