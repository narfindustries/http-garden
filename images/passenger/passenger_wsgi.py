import flask
import base64
import werkzeug.routing

application = flask.Flask(__name__)
application.url_map.add(werkzeug.routing.Rule("/", endpoint="index"))


@application.endpoint("index")
def hello() -> str:
    headers: str = (
        b",".join(
            b'["'
            + base64.b64encode(k.encode("latin1"))
            + b'","'
            + base64.b64encode(v.encode("latin1"))
            + b'"]'
            for k, v in flask.request.headers
        )
    ).decode("latin1")
    uri: str = base64.b64encode((flask.request.full_path[:-1] if len(flask.request.query_string) == 0 else flask.request.full_path).encode("latin1")).decode("latin1")
    method: str = base64.b64encode(flask.request.method.encode("latin1")).decode("latin1")
    body: str = base64.b64encode(flask.request.data).decode("latin1")
    version: str = ""
    return f'{{"headers":[{headers}],"uri":"{uri}","method":"{method}","body":"{body}","version":"{version}"}}'


if __name__ == "__main__":
    application.run()
