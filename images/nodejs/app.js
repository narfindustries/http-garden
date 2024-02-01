require('http').createServer((request, response) => {
    let body = [];
    request.on('data', (chunk) => {
        body.push(chunk);
    }).on('end', () => {
        response.end(JSON.stringify({
            "headers": Object.keys(request.headers).map((key) => [btoa(key), btoa(request.headers[key])]),
            "body": Buffer.concat(body).toString('base64'),
            "uri": btoa(request.url),
            "method": btoa(request.method),
            "version": btoa(request.httpVersion),
        }));
    });
}).listen(80);
