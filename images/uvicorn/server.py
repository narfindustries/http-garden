from base64 import b64encode


async def read_body(receive) -> bytes:
    """
    Read and return the entire body from an incoming ASGI message.
    """
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body


async def app(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
            ],
        }
    )
    body: bytes = (
        b'{"method":"'
        + b64encode(scope["method"].encode("latin1"))
        + b'","version":"'
        + b64encode(scope["http_version"].encode("latin1"))
        + b'","uri":"'
        + b64encode(
            scope["raw_path"]
            + ((b"?" + scope["query_string"]) if scope["query_string"] else b"")
        )
        + b'","body":"'
        + b64encode(await read_body(receive))
        + b'","headers":['
        + b",".join(
            b'["' + b64encode(k) + b'","' + b64encode(v) + b'"]'
            for k, v in scope["headers"]
        )
        + b"]}"
    )
    await send(
        {
            "type": "http.response.body",
            "body": body,
        }
    )
