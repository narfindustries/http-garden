from base64 import b64encode

from twisted.web import server, resource
from twisted.internet import reactor

class TheResource(resource.Resource):
    isLeaf = True
    def render(self, request) -> bytes:
        result: bytes = b'{"headers":['
        result += b",".join(b'["' + b64encode(name) + b'","' + b64encode(value) + b'"]' for name, value in request.getAllHeaders().items())
        result += b'],"method":"' + b64encode(request.method)
        result += b'","uri":"' + b64encode(request.uri)
        result += b'","version":"' + b64encode(request.clientproto)
        result += b'","body":"' + b64encode(request.content.read())
        result += b'"}'
        return result

site = server.Site(TheResource())
reactor.listenTCP(80, site)
reactor.run()
