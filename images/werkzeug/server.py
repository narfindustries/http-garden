from werkzeug.wrappers import Request, Response
from base64 import b64encode


@Request.application
def application(request):
    return Response(
        (b'{"headers":['
        + b",".join(b'["' + b64encode(k.encode("latin1")) + b'","' + b64encode(v.encode("latin1")) + b'"]' for k, v in request.headers.items())
        + b'],"body":"'
        + b64encode(request.data)
        + b'","method":"'
        + b64encode(request.method.encode("latin1"))
        + b'","uri":"'
        + b64encode((request.full_path[:-1] if len(request.query_string) == 0 else request.full_path).encode("latin1"))
        + b'","version":""}').decode("latin1")
    )


if __name__ == "__main__":
    from werkzeug.serving import run_simple, WSGIRequestHandler
    WSGIRequestHandler.protocol_version = "HTTP/1.1"

    run_simple("0.0.0.0", 80, application)
