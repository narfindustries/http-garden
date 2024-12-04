# The HTTP Garden
The HTTP Garden is a collection of HTTP servers and proxies configured to be composable, along with scripts to interact with them in a way that makes finding vulnerabilities much much easier. For some cool demos of the vulnerabilities that you can find with the HTTP Garden, check out [our ShmooCon 2024 talk](https://youtube.com/watch?v=aKPAX00ft5s&t=2h19m0s).

## Acknowledgements

We'd like to thank our friends at [Galois](https://galois.com), [Trail of Bits](https://www.trailofbits.com/), [Narf Industries](https://narfindustries.com/), and [Dartmouth College](https://web.cs.dartmouth.edu/) for making this project possible.

This material is based upon work supported by the Defense Advanced Research Projects Agency (DARPA) under contract number HR0011-19-C-0076.

## Getting Started

### Dependencies
0. The HTTP Garden runs on x86_64 Linux, and is untested on other platforms.
1. The target servers are built and run in Docker containers, so you'll need Docker.
2. You'll also need the following Python packages, which you can get from PyPI (i.e. with `pip`) or from your system package manager:
- `docker`
  - For interacting with Docker
- `pyyaml`
  - For parsing yaml
- `tqdm`
  - For progress bars

If you're installing Python packages with your system package manager, be aware that the package names may need to be prefixed with `py3-`, `python3-`, or `python-`, depending on the system.

3. I also highly recommend installing [rlwrap](https://github.com/hanslub42/rlwrap) from your package manager, because it makes the Garden repl a whole lot more fun.

### Building
- Build the base image:
```sh
docker build ./images/http-garden-soil -t http-garden-soil
```
This image contains some basic utilities, plus a forked AFL++ that facilitates collecting coverage from processes without killing them.

- Build some HTTP servers and proxies:
```sh
docker compose build gunicorn hyper nginx haproxy nginx_proxy
```

There are, of course, way more targets in the HTTP garden than the ones we just built. It's just that building them all takes a long time. Even building these few will take a few minutes!

### Running
- Start up some servers and proxies:
```sh
docker compose up gunicorn hyper nginx haproxy nginx_proxy
```
- Start the repl:
```sh
rlwrap python3 tools/repl.py
```
- Filter a basic GET request through [HAProxy](https://github.com/haproxy/haproxy), then through an [Nginx](https://github.com/nginx/nginx) reverse proxy, then send the result to [Gunicorn](https://github.com/benoitc/gunicorn), [Hyper](https://github.com/hyperium/hyper/), and [Nginx](https://github.com/nginx/nginx) origin servers, and display whether their interpretations match:
```
garden> payload 'GET / HTTP/1.1\r\nHost: whatever\r\n\r\n' # Set the payload
garden> transduce haproxy nginx_proxy # Run the payload through the reverse proxies
[1]: 'GET / HTTP/1.1\r\nHost: whatever\r\n\r\n'
    ⬇️ haproxy
[2]: 'GET / HTTP/1.1\r\nhost: whatever\r\n\r\n'
    ⬇️ nginx_proxy
[3]: 'GET / HTTP/1.1\r\nHost: echo\r\nConnection: close\r\n\r\n'
garden> servers gunicorn hyper nginx # Select the servers
garden> grid # Show their interpretations
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
Seems like they all agree. Let's try a more interesting payload:
```
garden> payload 'POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0\n\r\n'
garden> grid
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
There's a discrepancy! This is because Nginx supports `\n` as a line ending in chunk lines, but Hyper and Gunicorn don't. Nginx is technically violating RFC 9112 here, but the impact is likely minimal.

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
- `update.py`: A script that updates the commit hashes in `docker-compose.yml`,
- ...and a few more scripts that aren't user-facing.

## Targets

### HTTP Servers
| Name | Runs locally? | Coverage Collected? |
| ---- | ------------- | ------------------- |
| [aiohttp](https://github.com/aio-libs/aiohttp) | yes | yes |
| [apache_httpd](https://github.com/apache/httpd) | yes | yes |
| [apache_tomcat](https://github.com/apache/tomcat) | yes | no |
| [cheroot](https://github.com/cherrypy/cheroot) | yes | yes |
| [cpp_httplib](https://github.com/yhirose/cpp-httplib) | yes | no |
| [dart_stdlib](https://github.com/dart-lang/sdk) | yes | no |
| [eclipse_grizzly](https://github.com/eclipse-ee4j/grizzly) | yes | no |
| [eclipse_jetty](https://github.com/eclipse/jetty.project) | yes | no |
| [fasthttp](https://github.com/valyala/fasthttp) | yes | no |
| [go_stdlib](https://github.com/golang/go) | yes | no |
| [gunicorn](https://github.com/benoitc/gunicorn) | yes | yes |
| [h2o](https://github.com/h2o/h2o.git) | yes | yes |
| [haproxy_fcgi](https://github.com/haproxy/haproxy) | yes | no |
| [hyper](https://github.com/hyperium/hyper) | yes | no |
| [hypercorn](https://github.com/pgjones/hypercorn) | yes | yes |
| [ktor](https://github.com/ktorio/ktor) | yes | no |
| [libevent](https://github.com/libevent/libevent) | yes | no |
| [libmicrohttpd](https://git.gnunet.org/libmicrohttpd.git) | yes | no |
| [libsoup](https://gitlab.gnome.org/GNOME/libsoup.git) | yes | no |
| [lighttpd](https://github.com/lighttpd/lighttpd1.4) | yes | yes |
| [mongoose](https://github.com/cesanta/mongoose) | yes | yes |
| [netty](https://github.com/netty/netty) | yes | no |
| [nginx](https://github.com/nginx/nginx) | yes | yes |
| [node_stdlib](https://github.com/nodejs/node) | yes | no |
| [openlitespeed](https://github.com/litespeedtech/openlitespeed) | yes | no |
| [openwrt_uhttpd](https://git.openwrt.org/project/uhttpd.git) | yes | yes |
| [php_stdlib](https://github.com/php/php-src) | yes | no |
| [phusion_passenger](https://github.com/phusion/passenger) | yes | no |
| [protocol_http1](https://github.com/socketry/protocol-http1) | yes | no |
| [puma](https://github.com/puma/puma) | yes | no |
| [servicetalk](https://github.com/apple/servicetalk) | yes | no |
| [tornado](https://github.com/tornadoweb/tornado) | yes | no |
| [twisted](https://github.com/twisted/twisted) | yes | no |
| [undertow](https://github.com/undertow-io/undertow) | yes | no |
| [uvicorn](https://github.com/encode/uvicorn) | yes | yes |
| [waitress](https://github.com/Pylons/waitress) | yes | yes |
| [webrick](https://github.com/ruby/webrick) | yes | no |
| [yahns](https://yhbt.net/yahns.git) | yes | no |
| iis  | no | no |
| openbsd_httpd  | no | no |

### HTTP Transducers
| Name | Runs locally? |
| ---- | ------------- |
| [spring_cloud_gateway](https://github.com/spring-cloud/spring-cloud-gateway) | yes |
| [apache_httpd_proxy](https://github.com/apache/httpd) | yes |
| [apache_traffic_server](https://github.com/apache/trafficserver) | yes |
| [go_stdlib_proxy](https://github.com/golang/go) | yes |
| [h2o_proxy](https://github.com/h2o/h2o.git) | yes |
| [haproxy](https://github.com/haproxy/haproxy) | yes |
| [haproxy_invalid](https://github.com/haproxy/haproxy) | yes |
| [lighttpd_proxy](https://github.com/lighttpd/lighttpd1.4) | yes |
| [nginx_proxy](https://github.com/nginx/nginx) | yes |
| [openlitespeed_proxy](https://github.com/litespeedtech/openlitespeed) | yes |
| [pingora](https://github.com/cloudflare/pingora) | yes |
| [pound](https://github.com/graygnuorg/pound) | yes |
| [squid](https://github.com/squid-cache/squid) | yes |
| [varnish](https://github.com/varnishcache/varnish-cache) | yes |
| [yahns_proxy](https://yhbt.net/yahns.git) | yes |
| akamai | no |
| awselb_classic | no |
| awselb_application | no |
| cloudflare | no |
| google_classic | no |
| google_global | no |
| iis_proxy | no |
| openbsd_relayd | no |

### Omissions

The following are explanations for a few notable omissions from the Garden:
| Name | Rationale |
| [unicorn](https://yhbt.net/unicorn.git/) | Doesn't support connection reuse, and uses the same parser as `yahns`. |
| [SwiftNIO](https://github.com/apple/swift-nio) | Uses `llhttp` for HTTP parsing, which is already covered by `node_stdlib`. |
| [Bun](https://github.com/oven-sh/bun) | Uses `picohttpparser` for HTTP parsing, which is already covered by `h2o`. |
| [Deno](https://github.com/denoland/deno) | Uses `hyper` for HTTP parsing, which is already in the Garden. |
| [Daphne](https://github.com/django/daphne) | Uses `twisted` for HTTP parsing, which is already in the Garden. |
| [pitchfork](https://github.com/Shopify/pitchfork) | Uses the same parser as `yahns`. |
| [nghttpx](https://github.com/nghttp2/nghttp2) | Uses `lhttp` for HTTP parsing, which is already covered by `node_stdlib`. |
| [CherryPy](https://github.com/cherrypy/cherrypy) | Uses `cheroot` for HTTP parsing, which is already in the Garden. |

## Results

See TROPHIES.md for a complete list of bugs that the Garden has found.
