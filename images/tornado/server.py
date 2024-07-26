import asyncio
import base64

import tornado


class CaseInsensitiveBagOfAllStringsExcept:
    def __init__(self, exceptions: list[str]):
        self.exceptions = [s.lower() for s in exceptions]
    def __contains__(self, thing):
        return thing.lower() not in self.exceptions


class Handler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = CaseInsensitiveBagOfAllStringsExcept(dir(tornado.web.RequestHandler))
    _new_cookie = {}

    def __getattr__(self, key: str):
        return self._handle

    def _handle(self, *args, **kwargs) -> None:
        method: bytes = base64.b64encode(self.request.method.encode("latin1"))
        version: bytes = base64.b64encode(self.request.version.encode("latin1"))
        uri: bytes = base64.b64encode(self.request.uri.encode("latin1"))
        body: bytes = base64.b64encode(self.request.body)

        response_body: bytes = (
            b'{"headers":['
            + b",".join(
                b'["'
                + base64.b64encode(k.encode("latin1"))
                + b'","'
                + base64.b64encode(v.encode("latin1"))
                + b'"]'
                for k, v in self.request.headers.get_all()
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
        self.write(response_body)

    # This has to be special-cased because tornado/web.py:275-281 sets them to unimplemented
    head = get = post = delete = patch = put = options = _handle


async def main():
    app = tornado.web.Application([(r".*", Handler)])
    app.listen(80)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    import afl

    afl.init()
    asyncio.run(main())
