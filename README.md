# The HTTP Garden
The HTTP Garden is a collection of HTTP servers and proxies configured to be composable, along with scripts to interact with them in a way that makes finding vulnerabilities much much easier. For some cool demos of the vulnerabilities that you can find with the HTTP Garden, check out [our ShmooCon 2024 talk](https://youtube.com/watch?v=aKPAX00ft5s&t=2h19m0s).

## Acknowledgements

We'd like to thank our friends at [Galois](https://galois.com), [Trail of Bits](https://www.trailofbits.com/), [Narf Industries](https://narfindustries.com/), and [Dartmouth College](https://web.cs.dartmouth.edu/) for making this project possible.

This material is based upon work supported by the Defense Advanced Research Projects Agency (DARPA) under contract number HR0011-19-C-0076.

## Getting Started

### Dependencies
0. The HTTP Garden runs on x86\_64 and AArch64 Linux, and is untested on other platforms.
1. The target servers are built and run in Docker containers, so you'll need Docker.
2. You'll also need Python 3.12+ and the following Python packages, which you can get from PyPI (i.e. with `pip`) or from your system package manager:
- `docker`
  - For interacting with Docker
- `pyyaml`
  - For parsing yaml
- `tqdm`
  - For progress bars

If you're installing Python packages with your system package manager, be aware that the package names may need to be prefixed with `py3-`, `python3-`, or `python-`, depending on the system.

### Running
- Build and start up some servers and proxies:
```sh
./garden.sh start --build gunicorn hyper nginx haproxy
```
- From another shell, start the repl:
```sh
./garden.sh repl
```
- Send a basic GET request through [HAProxy](https://github.com/haproxy/haproxy), then send the result to [Gunicorn](https://github.com/benoitc/gunicorn), [Hyper](https://github.com/hyperium/hyper/), and [Nginx](https://github.com/nginx/nginx) origin servers, and display whether their interpretations match:
```
garden> payload 'GET / HTTP/1.1\r\nHOST: a\r\n\r\n' | transduce haproxy | fanout | grid
'GET / HTTP/1.1\r\nHOST: a\r\n\r\n'
⬇️ haproxy
'GET / HTTP/1.1\r\nhost: a\r\n\r\n'
gunicorn: [
    HTTPRequest(
        method=b'GET', uri=b'/', version=b'1.1',
        headers=[
            (b'host', b'a'),
        ],
        body=b'',
    ),
]
hyper: [
    HTTPRequest(
        method=b'GET', uri=b'/', version=b'1.1',
        headers=[
            (b'host', b'a'),
        ],
        body=b'',
    ),
]
nginx: [
    HTTPRequest(
        method=b'GET', uri=b'/', version=b'1.1',
        headers=[
            (b'host', b'a'),
            (b'content-length', b''),
            (b'content-type', b''),
        ],
        body=b'',
    ),
]
         g
         u
         n
         i h n
         c y g
         o p i
         r e n
         n r x
        +-----
gunicorn|✓ ✓ ✓
hyper   |  ✓ ✓
nginx   |    ✓
```
Seems like they all agree. (Note that even though Nginx added `content-length` and `content-type` headers, the Garden is aware of this and does not let this insignificant discrepancy show up in `grid` output.)

Let's try a payload that uses a bare LF line ending in a chunked message body. This is [disallowed in the spec](https://www.rfc-editor.org/errata/eid7633).
```
garden> payload 'POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0\n\r\n' | fanout | grid
gunicorn: [
    HTTPResponse(version=b'1.1', method=b'400', reason=b'Bad Request'),
]
hyper: [
]
nginx: [
    HTTPRequest(
        method=b'POST', uri=b'/', version=b'1.1',
        headers=[
            (b'transfer-encoding', b'chunked'),
            (b'host', b'a'),
            (b'content-length', b'0'),
            (b'content-type', b''),
        ],
        body=b'',
    ),
]
         g
         u
         n
         i h n
         c y g
         o p i
         r e n
         n r x
        +-----
gunicorn|✓ ✓ X
hyper   |  ✓ X
nginx   |    ✓
```
Okay, so Gunicorn responded 400, Hyper didn't respond, and Nginx accepted.
This is a violation of the spec by the Nginx authors that [they don't care to fix](https://mailman.nginx.org/pipermail/nginx-devel/2024-January/5CQQCHFYQMXTBAK7H2FITLVQQS5ECFFM.html).

You may also have noticed that even though Gunicorn and Hyper didn't have exactly the same response, they showed as agreeing in the `grid` output earlier.
This is because their responsees are essentially equivalent (a rejection of the message), and the Garden takes this into account.

## Directory Layout
### `images`
The `images` directory contains a subdirectory for each HTTP server and transducer in the Garden.
Each target gets its own Docker image.
All programs are built from source when possible.
So that we can easily build multiple versions of each target, all targets are paremetrized with a repository URL (`APP_REPO`), branch name (`APP_BRANCH`), and commit hash (`APP_VERSION`).

### `tools`
The `tools` directory contains the scripts that are used to interact with the servers. Inside it, you'll find
- `diagnose_anomalies.py`: A script for enumerating benign HTTP parsing quirks in the systems under test to be ignored during fuzzing,
- `repl.py`: The primary user interface to the HTTP Garden,
- `update.py`: A script for updating the commit hashes in `docker-compose.yml`,
- ...and a few more scripts that aren't user-facing.

## Targets

### HTTP Servers
| Name |
|-|
| [aiohttp](https://github.com/aio-libs/aiohttp) |
| [apache_httpd](https://github.com/apache/httpd) |
| [apache_tomcat](https://github.com/apache/tomcat) |
| [appweb](https://github.com/embedthis/appweb) |
| [aws_c_http](https://github.com/awslabs/aws-c-http) |
| [cpp_httplib](https://github.com/yhirose/cpp-httplib) |
| [eclipse_grizzly](https://github.com/eclipse-ee4j/grizzly) |
| [eclipse_jetty](https://github.com/eclipse/jetty.project) |
| [fasthttp](https://github.com/valyala/fasthttp) |
| [go_stdlib](https://github.com/golang/go) |
| [gunicorn](https://github.com/benoitc/gunicorn) |
| [h2o](https://github.com/h2o/h2o.git) |
| [haproxy_fcgi](https://github.com/haproxy/haproxy) |
| [hyper](https://github.com/hyperium/hyper) |
| [hypercorn](https://github.com/pgjones/hypercorn) |
| [ktor](https://github.com/ktorio/ktor) |
| [libevent](https://github.com/libevent/libevent) |
| [libmicrohttpd](https://git.gnunet.org/libmicrohttpd.git) |
| [libsoup](https://gitlab.gnome.org/GNOME/libsoup.git) |
| [lighttpd](https://github.com/lighttpd/lighttpd1.4) |
| [mongoose](https://github.com/cesanta/mongoose) |
| [netty](https://github.com/netty/netty) |
| [nginx](https://github.com/nginx/nginx) |
| [node_stdlib](https://github.com/nodejs/node) |
| [openbsd_httpd](https://github.com/kenballus/obhttpd-linux) |
| [openlitespeed](https://github.com/litespeedtech/openlitespeed) |
| [protocol_http1](https://github.com/socketry/protocol-http1) |
| [puma](https://github.com/puma/puma) |
| [tornado](https://github.com/tornadoweb/tornado) |
| [twisted](https://github.com/twisted/twisted) |
| [undertow](https://github.com/undertow-io/undertow) |
| [uvicorn](https://github.com/encode/uvicorn) |
| [waitress](https://github.com/Pylons/waitress) |
| [webrick](https://github.com/ruby/webrick) |
| [yahns](https://yhbt.net/yahns.git) |

### HTTP Transducers
| Name |
|-|
| [apache_httpd_proxy](https://github.com/apache/httpd) |
| [apache_traffic_server](https://github.com/apache/trafficserver) |
| [envoy](https://github.com/envoyproxy/envoy) |
| [go_stdlib_proxy](https://github.com/golang/go) |
| [h2o_proxy](https://github.com/h2o/h2o.git) |
| [haproxy](https://github.com/haproxy/haproxy) |
| [lighttpd_proxy](https://github.com/lighttpd/lighttpd1.4) |
| [nghttpx](https://github.com/nghttp2/nghttp2) |
| [nginx_proxy](https://github.com/nginx/nginx) |
| [openlitespeed_proxy](https://github.com/litespeedtech/openlitespeed) |
| [pound](https://github.com/graygnuorg/pound) |
| [squid](https://github.com/squid-cache/squid) |
| [varnish](https://github.com/varnishcache/varnish-cache) |
| [yahns_proxy](https://yhbt.net/yahns.git) |

### Omissions

The following are explanations for a few notable omissions from the Garden:

| Name | Rationale |
| ---- | --------- |
| Anything from Microsoft | MSRC told us "HTTP smuggling is not consider a vulnerability," and I feel no particular need to help Microsoft. |
| [unicorn](https://yhbt.net/unicorn.git/) | Uses the same HTTP parser as `yahns`. |
| [SwiftNIO](https://github.com/apple/swift-nio) | Uses `llhttp` for HTTP parsing, which is already covered by `node_stdlib`. |
| [Bun](https://github.com/oven-sh/bun) | Uses `picohttpparser` for HTTP parsing, which is already covered by `h2o`. |
| [Deno](https://github.com/denoland/deno) | Uses `hyper` for HTTP parsing, which is already in the Garden. |
| [Daphne](https://github.com/django/daphne) | Uses `twisted` for HTTP parsing, which is already in the Garden. |
| [pitchfork](https://github.com/Shopify/pitchfork) | Uses the same parser as `yahns`. |
| [nghttpx](https://github.com/nghttp2/nghttp2) | Uses `lhttp` for HTTP parsing, which is already covered by `node_stdlib`. |
| [Cheroot](https://github.com/cherrypy/cheroot) | [Ignores our reports](https://github.com/cherrypy/cheroot/issues?q=is%3Aissue%20state%3Aopen%20author%3Akenballus). |
| [CherryPy](https://github.com/cherrypy/cherrypy) | Uses `cheroot` for HTTP parsing. |
| [libhttpserver](https://github.com/etr/libhttpserver) | Uses `libmicrohttpd` for HTTP parsing, which is already in the Garden. |
| [Werkzeug](https://github.com/pallets/werkzeug) | Uses the CPython stdlib for HTTP parsing, which is already in the Garden.
| [Caddy](https://github.com/caddyserver/caddy) | Uses the Go stdlib for HTTP parsing, which is already in the Garden. |
| [Tengine](https://github.com/alibaba/tengine) | Uses Nginx's HTTP parser. |
| [OpenResty](https://github.com/openresty/openresty) | Uses Nginx's HTTP parser. |
| [Google Cloud Global External Application Load Balancer](https://cloud.google.com/load-balancing/docs/https) | Based on Envoy. |
| [Google Cloud Regional External Application Load Balancer](https://cloud.google.com/load-balancing/docs/https) | Based on Envoy. |
| [Phusion Passenger](https://github.com/phusion/passenger) | Uses `llhttpd` for HTTP parsing, which is already covered by `node_stdlib`. |
| [passim](https://github.com/hughsie/passim/) | Uses `libsoup` for HTTP parsing, which is already in the Garden. |
| [boa](http://boa.org) | Unmaintained. |
| [Ulfius](https://github.com/babelouest/ulfius) | Uses libmicrohttpd, which is already in the Garden. |
| [Vultr Load Balancer](https://my.vultr.com/loadbalancers/) | It's just HAProxy, which is already in the Garden. |
| [VMWare Avi Load Balancer](https://www.vmware.com/products/cloud-infrastructure/avi-load-balancer) | It's just Nginx, which is already in the Garden. |
| [Sanic](https://github.com/sanic-org/sanic) | Uses httptools, which is already covered by Uvicorn. |
| [openwrt uhttpd](https://github.com/openwrt/uhttpd) | [Ignores our reports](https://github.com/openwrt/uhttpd/issues?q=is%3Aissue%20state%3Aopen%20author%3Akenballus) |
| [CPython http.server](https://github.com/python/cpython) | Not intended for production use. |
| [Cheroot](https://github.com/cherrypy/cheroot) | Has too many bugs. Would consider reintroducing in the future. |
| [openjdk_stdlib](https://github.com/openjdk/jdk) | Provides no coherent vulnerability disclosure channel. |
| [gevent](https://github.com/gevent/gevent) | Not intended for production use. See [this issue](https://github.com/gevent/gevent/commit/cbb527d3096502ae251f83002e4a4c0c024c18a9). |
| [dart_stdlib](https://github.com/dart-lang/sdk) | Ignored prior reports. |

## Results

See TROPHIES.md for a complete list of bugs that the Garden has found.
