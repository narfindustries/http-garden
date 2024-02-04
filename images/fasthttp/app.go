package main

import (
    "encoding/base64"
    "fmt"
    "net/http"
    "io"
    "log"

    "github.com/valyala/fasthttp"
    "github.com/valyala/fasthttp/fasthttpadaptor"
)

// This uses fasthttp's net/http interop. We may want to consider porting to the native API in the future.

func handle_request(w http.ResponseWriter, req *http.Request) {
    body, err := io.ReadAll(req.Body)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    fmt.Fprintf(w, "{\"headers\":[")
    first := true
    for key, headers := range req.Header {
        for _, value := range headers {
            if !first {
                fmt.Fprintf(w, "%s", ",");
            }
            first = false
            fmt.Fprintf(w, "[\"%s\",\"%s\"]", base64.StdEncoding.EncodeToString([]byte(key)), base64.StdEncoding.EncodeToString([]byte(value)))
        }
    }
    for _, encoding := range req.TransferEncoding {
        if !first {
            fmt.Fprintf(w, "%s", ",");
        }
        first = false
        fmt.Fprintf(w, "[\"dHJhbnNmZXItZW5jb2Rpbmc=\",\"%s\"]", base64.StdEncoding.EncodeToString([]byte(encoding)))
    }
    fmt.Fprintf(w, "],")

    fmt.Fprintf(w, "\"body\":\"%s\",", base64.StdEncoding.EncodeToString(body))
    fmt.Fprintf(w, "\"method\":\"%s\",", base64.StdEncoding.EncodeToString([]byte(req.Method)))
    fmt.Fprintf(w, "\"version\":\"%s\",", base64.StdEncoding.EncodeToString([]byte(req.Proto)))
    fmt.Fprintf(w, "\"uri\":\"%s\"}", base64.StdEncoding.EncodeToString([]byte(req.URL.String())))
}

func main() {
    h := fasthttpadaptor.NewFastHTTPHandler(http.HandlerFunc(handle_request))

    if err := fasthttp.ListenAndServe("0.0.0.0:80", h); err != nil {
        log.Fatalf("Error in ListenAndServe: %v", err)
    }
}
