var http = require('http');

http.createServer(onRequest).listen(80);

function onRequest(client_request, client_response) {
  var proxy = http.request({
    hostname: 'PROXY_BACKEND_PLACEHOLDER',
    port: 80,
    path: client_request.url,
    method: client_request.method,
    headers: client_request.headers
  }, (response) => {
    client_response.writeHead(response.statusCode, response.headers)
    response.pipe(client_response, { end: true });
  });

  client_request.pipe(proxy, { end: true });
}
