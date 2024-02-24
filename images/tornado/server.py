import asyncio
import base64

from tornado.httpserver import HTTPServer
from tornado.httputil import HTTPServerRequest


def handle_request(req: HTTPServerRequest) -> None:
    method: bytes = base64.b64encode(req.method.encode("latin1"))
    version: bytes = base64.b64encode(req.version.encode("latin1"))
    uri: bytes = base64.b64encode(req.uri.encode("latin1"))
    body: bytes = base64.b64encode(req.body)

    response_body: bytes = (
        b'{"headers":['
        + b",".join(
            b'["'
            + base64.b64encode(k.encode("latin1"))
            + b'","'
            + base64.b64encode(v.encode("latin1"))
            + b'"]'
            for k, v in req.headers.get_all()
        )
        + b'],"body":"'
        + body
        + b'","method":"'
        + method
        + b'","uri":"'
        + uri
        + b'","version":"'
        + version
        + b'"}'
    )

    req.connection.write(
        b"HTTP/1.1 200 OK\r\n"
        + f"Content-Length: {len(response_body)}\r\n".encode("latin1")
        + b"\r\n"
        + response_body
    )


async def main():
    server = HTTPServer(handle_request)
    server.listen(80)
    await asyncio.Event().wait()


if __name__ == "__main__":
    import afl

    afl.init()
    asyncio.run(main())
