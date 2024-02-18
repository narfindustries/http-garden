function respond(request) {
    let headers = [];
    Object.keys(request.headersIn).forEach((key, _) => {
        headers.push([btoa(key), Buffer.from(request.headersIn[key]).toString("base64")])
    });
    let uri = "";
    try {
        uri = btoa(request.uri);
    }
    catch(_) {
        request.return(400, "HTTP/0.9 400 Bad URI\r\n\r\n");
    }

    let body = "";
    let method = "";
    let version = "";
    try {
        body = btoa(request.requestBuffer || "");
        method = btoa(request.method);
        version = btoa(request.httpVersion)
    }
    catch(_) {
        request.return(400, "HTTP/1.1 400 Bad URI\r\n\r\n");
    }
    request.return(200,
        JSON.stringify({
            "headers": headers,
            "body": body,
            "uri": uri,
            "method": method,
            "version": version
        })
    );
}

export default {
    respond
}
