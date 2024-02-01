function respond(request) {
    let headers = [];
    Object.keys(request.headersIn).forEach((key, _) => {
        headers.push([btoa(key), btoa(request.headersIn[key])])
    });
    let uri = ""
    try {
        uri = btoa(request.uri);
    }
    catch(_) {
        request.return(400, "HTTP/0.9 400 Bad URI\r\n\r\n");
    }
    let body = ""
    try {
        body = btoa(request.requestBuffer || "");
    }
    catch(_) {}
    request.return(200,
        JSON.stringify({
            "headers": headers,
            "body": body,
            "uri": uri,
            "method": btoa(request.method),
            "version": btoa(request.httpVersion)
        })
    );
}

export default {
    respond
}
