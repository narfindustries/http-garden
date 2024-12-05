from base64 import b64encode
from wsgiref.simple_server import make_server

RESERVED_HEADERS = ("CONTENT_LENGTH", "CONTENT_TYPE")

def app(environ, start_response) -> list[bytes]:
    response_body: bytes = (
        b'{"headers":['
        + b",".join(
            b'["'
            + b64encode(k.encode("latin1")[len("HTTP_") if k not in RESERVED_HEADERS else 0 :])
            + b'","'
            + b64encode(environ[k].encode("latin1"))
            + b'"]'
            for k in environ
            if k.startswith("HTTP_") or k in RESERVED_HEADERS
        )
        + b'],"body":"'
        + b64encode(environ["wsgi.input"].read())
        + b'","version":"'
        + b64encode(environ["SERVER_PROTOCOL"].encode("latin1"))
        + b'","uri":"'
        + b64encode(
            (
                environ["PATH_INFO"] + (("?" + environ["QUERY_STRING"]) if environ["QUERY_STRING"] else "")
            ).encode("latin1")
        )
        + b'","method":"'
        + b64encode(environ["REQUEST_METHOD"].encode("latin1"))
        + b'"}'
    )
    start_response(
        "200 OK", [("Content-Length", f"{len(response_body)}")]
    )
    return [response_body]


if __name__ == "__main__":
    with make_server('0.0.0.0', 80, app) as httpd:
        httpd.default_request_version = "HTTP/1.1"
        httpd.serve_forever()
