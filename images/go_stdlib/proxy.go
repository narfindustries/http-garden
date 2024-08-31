package main

import (
	"net/http"
	"net/http/httputil"
	"net/url"
)

func main() {
	url, _ := url.Parse("http://PROXY_BACKEND_PLACEHOLDER")
	proxy := httputil.NewSingleHostReverseProxy(url)
	http.HandleFunc("/", proxy.ServeHTTP)
	http.ListenAndServe(":80", nil)
}
