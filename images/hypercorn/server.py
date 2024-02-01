from base64 import b64encode

async def app(scope, receive, send):
    query: bytes = scope["query_string"]
    uri: bytes = scope["raw_path"]
    if len(query) > 0:
        uri += b"?" + query
    body: bytes = b""
    while True:
        chunk_dict = await receive()
        if "body" in chunk_dict:
            body += chunk_dict["body"]
            if len(chunk_dict["body"]) == 0:
                break
        else:
            break


    response_body: bytes = b'{"uri":"' + b64encode(uri) + \
                           b'","headers":[' + b','.join(b'["' + b64encode(k) + b'","' + b64encode(v) + b'"]' for k, v in scope["headers"]) + \
                           b'],"version":"' + b64encode(scope["http_version"].encode("latin1")) + \
                           b'","body":"' + b64encode(body) + b'"' + \
                           b',"method":"' + b64encode(scope["method"].encode("latin1")) + \
                           b'"}'
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            (b'content-length', str(len(response_body)).encode("latin1")),
        ],
    })
    await send({
        'type': 'http.response.body',
        'body': response_body,
    })
