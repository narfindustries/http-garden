from aiohttp import web
from aiohttp.web_protocol import RequestPayloadError
from base64 import b64encode


async def respond(request):
    try:
        body = await request.content.read()
    except RequestPayloadError:
        return web.Response(status=400, reason="Bad message body.")
    return web.Response(
        text=(
            b'{"headers":['
            + b",".join(
                b'["'
                + b64encode(k.encode("utf8", "surrogateescape"))
                + b'","'
                + b64encode(v.encode("utf8", "surrogateescape"))
                + b'"]'
                for k, v in request.headers.items()
            )
            + b'],"body":"'
            + b64encode(body)
            + b'","method":"'
            + b64encode(request.method.encode("utf8", "surrogateescape"))
            + b'","uri":"'
            + b64encode(request.raw_path.encode("utf8", "surrogateescape"))
            + b'","version":"'
            + b64encode(str(request.version.major).encode('latin1') + b'.' + str(request.version.minor).encode('latin1'))
            + b'"}'
        ).decode("latin1")
    )


app = web.Application()
app.add_routes([web.route("*", "/{unused_required_name:.*}", respond)])

import afl
afl.init()
web.run_app(app, port=80)
