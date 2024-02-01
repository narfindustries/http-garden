import asyncio
import tornado
import base64


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        method = base64.b64encode(self.request.method.encode("latin1")).decode("latin1")
        uri = base64.b64encode(self.request.uri.encode("latin1")).decode("latin1")
        version = base64.b64encode(self.request.version.encode('latin1')).decode("latin1")
        self.write('{"headers":[')
        self.write(
            ",".join(
                f'["{base64.b64encode(k.encode("latin1")).decode("latin1")}","{base64.b64encode(v.encode("latin1")).decode("latin1")}"]'
                for k, v in self.request.headers.get_all()
            )
        )
        self.write(
            f'],"body":"{base64.b64encode(self.request.body).decode("latin1")}","method":"{method}","uri":"{uri}","version":"{version}"}}'
        )

    post = head = delete = patch = put = options = get


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
        ]
    )


async def main():
    make_app().listen(80)
    await asyncio.Event().wait()


if __name__ == "__main__":
    import afl
    afl.init()
    asyncio.run(main())
