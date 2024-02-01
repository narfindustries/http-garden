package main

import (
    "encoding/base64"
    "fmt"
    "net/http"
    "io"
    "strings"
)

func handle_request(w http.ResponseWriter, req *http.Request) {
    body, err := io.ReadAll(req.Body)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    fmt.Fprintf(w, "{\"headers\":[")
    i := 1
    for canonical_key, headers := range req.Header {
        j := 1
        for _, value := range headers {
            fmt.Fprintf(w, "[\"%s\",\"%s\"]", base64.StdEncoding.EncodeToString([]byte(canonical_key)), base64.StdEncoding.EncodeToString([]byte(value)))
            if i != len(req.Header) || j != len(headers) {
                fmt.Fprintf(w, "%s", ",")
            }
            j = j + 1
        }
        i = i + 1
    }
    if req.Host != "" {
        if i > 1 {
            fmt.Fprintf(w, ",")
        }
        i = i + 1
        fmt.Fprintf(w, "[\"SG9zdA==\",\"%s\"]", base64.StdEncoding.EncodeToString([]byte(req.Host)))
    }
    if len(req.TransferEncoding) != 0 {
        if i > 1 {
            fmt.Fprintf(w, ",")
        }
        i = i + 1
        fmt.Fprintf(w, "[\"VHJhbnNmZXItRW5jb2Rpbmc=\",\"%s\"]", base64.StdEncoding.EncodeToString([]byte(strings.Join(req.TransferEncoding[:], ","))))
    }
    fmt.Fprintf(w, "],")
    fmt.Fprintf(w, "\"body\":\"%s\",", base64.StdEncoding.EncodeToString(body))
    fmt.Fprintf(w, "\"method\":\"%s\",", base64.StdEncoding.EncodeToString([]byte(req.Method)))
    fmt.Fprintf(w, "\"version\":\"%s\",", base64.StdEncoding.EncodeToString([]byte(req.Proto)))
    fmt.Fprintf(w, "\"uri\":\"%s\"}", base64.StdEncoding.EncodeToString([]byte(req.URL.String())))
}

func main() {
    s := &http.Server{
        Addr: "0.0.0.0:80",
        Handler: http.HandlerFunc(handle_request),
        MaxHeaderBytes: 1 << 20,
    }

    s.ListenAndServe()
}
