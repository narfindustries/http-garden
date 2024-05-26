# The HTTP Garden
The HTTP Garden is a collection of HTTP servers and proxies configured to be composable, along with scripts to interact with them in a way that makes finding vulnerabilities much much easier. For some cool demos of the vulnerabilities that you can find with the HTTP Garden, check out [our ShmooCon 2024 talk](https://yewtu.be/watch?v=aKPAX00ft5s&t=2h19m0s).

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
- Filter a basic GET request through [HAProxy](https://github.com/haproxy/haproxy), then through [Nginx](https://github.com/nginx/nginx) acting as a reverse proxy, then send the result to [Gunicorn](https://github.com/benoitc/gunicorn), [Hyper](https://github.com/hyperium/hyper/), and [Nginx](https://github.com/nginx/nginx), and display whether their interpretations match:
```
garden> payload 'GET / HTTP/1.1\r\nHost: whatever\r\n\r\n' # Set the payload
garden> transduce haproxy nginx_proxy # Run the payload through HAProxy and Nginx
[1]: 'GET / HTTP/1.1\r\nHost: whatever\r\n\r\n'
    ⬇️ haproxy
[2]: 'GET / HTTP/1.1\r\nhost: whatever\r\n\r\n'
    ⬇️ nginx_proxy
[3]: 'GET / HTTP/1.1\r\nHost: echo\r\nConnection: close\r\n\r\n'
garden> servers gunicorn hyper nginx # Select the servers
garden> grid
         gunicorn hyper    nginx
gunicorn          ✅       ✅
hyper                      ✅
nginx
```
Seems like they all agree. Let's try a more interesting payload:
```
garden> payload 'POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0\n\r\n'
garden> grid
         gunicorn hyper    nginx
gunicorn          ✅       ❌
hyper                      ❌
nginx
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
| ------------ | ------------ | ------- |
| aiohttp      | master       | yes     |
| apache       | trunk        | yes     |
| cherrypy     | main         | no      |
| daphne       | main         | yes     |
| deno         | main         | no      |
| fasthttp     | master       | no      |
| go_net_http  | master       | no      |
| gunicorn     | master       | no      |
| h2o          | master       | yes     |
| haproxy_fcgi | master       | no      |
| hyper        | master       | no      |
| hypercorn    | main         | no      |
| jetty        | jetty-12.0.x | no      |
| libevent     | master       | no      |
| libsoup      | master       | no      |
| lighttpd     | master       | yes     |
| mongoose     | master       | yes     |
| nginx        | default      | yes     |
| nodejs       | main         | no      |
| passenger    | stable-6.0   | no      |
| proxygen     | main         | no      |
| puma         | master       | no      |
| tomcat       | main         | no      |
| tornado      | master       | yes     |
| uhttpd       | master       | yes     |
| unicorn      | master       | no      |
| uvicorn      | master       | yes     |
| waitress     | main         | yes     |
| webrick      | master       | no      |
| werkzeug     | main         | no      |

### HTTP Proxies
| Name              | Version |
| ----------------- | ------- |
| apache_proxy      | trunk   |
| ats               | master  |
| caddy_proxy       | master  |
| go_net_http_proxy | master  |
| h2o_proxy         | master  |
| haproxy           | master  |
| haproxy_invalid   | master  |
| nghttpx           | master  |
| nginx_proxy       | default |
| pound             | master  |
| squid             | master  |
| varnish           | master  |

### External Targets
If you have external services (probably CDNs or servers that you can't run in Docker) that you want to add to the Garden, we do support that. See the bottom of `external-services.yml` for some more details on that.

## Bugs
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
  - Affected programs: A list of servers in which this bug is present, along with report and patch timelines. Since some implementation bugs are common, and this keeps them from cluttering the list :)

### Server Bugs
These are bugs in the way servers accept and interpret requests.

1. The Python `int` constructor is used to parse chunk-sizes, so `0x`, `_`, `+`, and `-` are misinterpreted.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets chunk-sizes as their longest valid prefix, but forwards them as-is.
  - Risk: Medium. See transducer bug 7.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0_2e\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - August 1, 2023: Reported via [GH security advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg).
      - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
    - Gunicorn:
      - August 1, 2023: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3047).
      - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).
    - Tornado:
      - August 2, 2023: Reported via [GH security advisory](https://github.com/tornadoweb/tornado/security/advisories/GHSA-qppv-j76h-2rpx).
      - August 10, 2023: Fixed in [commit](https://github.com/tornadoweb/tornado/commit/b7a5dd29bb02950303ae96055082c12a1ea0a4fe).
2. `\x00`, `\r`, or `\n` are incorrectly permitted in header values.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards these bytes in header values, or accepts and forwards `\n` as a header line terminator.
  - Risk: High. See transducer bugs 10, 12, and 16.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nHeader: v\n\x00\ralue\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - August 1, 2023: Reported via [GH security advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg).
      - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
    - Gunicorn:
      - January 31, 2024: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3144).
      - January 31, 2024: Remains unfixed.
    - Tornado:
      - August 11, 2023: Reported via [GH issue](https://github.com/tornadoweb/tornado/issues/3310).
      - January 31, 2024: Remains unfixed.
3. Whitespace is incorrectly stripped from the ends of header names.
  - Use case: Request smuggling
  - Requirements: A transducer that considers whitespace before the `:` to be part of the header name.
  - Risk: Low. I'm not aware of any vulnerable transducers, but James Kettle [says that at least one exists](https://portswigger.net/research/http-desync-attacks-request-smuggling-reborn).
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length : 34\r\n\r\nGET / HTTP/1.1\r\nHost: whatever\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - August 2, 2023: Reported via [GH security advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg).
      - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
    - CherryPy:
      - February 4, 2024: Reported via [GH issue](https://github.com/cherrypy/cherrypy/issues/2016).
      - February 4, 2024: Remains unfixed.
    - OpenLiteSpeed:
      - July 31, 2023: Reported via email.
      - August 10, 2023: Fixed in OLS 1.7.18.
      - August 14, 2023: Assigned [CVE-2023-40518](https://www.cve.org/CVERecord?id=CVE-2023-40518).
4. Whitespace is incorrectly stripped from the beginning of the first header name.
  - Use case: Request smuggling
  - Requirements: A transducer that considers whitespace at the beginning of the first header name to be part of the header name.
  - Risk: Low. I'm not aware of any vulnerable transducers.
  - Payload: `GET / HTTP/1.1\r\n\tContent-Length: 1\r\n\r\nX`
  - Affected programs:
    - AIOHTTP:
      - August 20, 2023: Reported via GH security advisory [comment](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg#advisory-comment-86438).
      - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
5. HTTP versions are interpreted as their longest valid prefix.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET /test HTTP/1.32\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - October 14, 2023: Reported via [GH issue](https://github.com/aio-libs/aiohttp/issues/7700) and [PR](https://github.com/aio-libs/aiohttp/pull/7701).
      - October 15, 2023: Fixed in [commit](https://github.com/aio-libs/aiohttp/commit/312f747de91f20fa33af03fd368f857fbd32f36a).
6. HTTP methods are interpreted as their longest valid prefix.
  - Use case: ACL bypass
  - Requirements: A transducer that forwards invalid method names as-is.
  - Risk: Medium. Explanation omitted because the corresponding bugs are not yet reported.
  - Payload: `G=":<>(e),[T];?" /get HTTP/1.1\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - October 14, 2023: Reported via [GH issue](https://github.com/aio-libs/aiohttp/issues/7700) and [PR](https://github.com/aio-libs/aiohttp/pull/7701).
      - October 15, 2023: Fixed in [commit](https://github.com/aio-libs/aiohttp/commit/312f747de91f20fa33af03fd368f857fbd32f36a).
7. URIs are not validated whatsoever.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET ! HTTP/1.1\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - October 16, 2023: Reported via [GH issue](https://github.com/aio-libs/aiohttp/issues/7712).
      - October 16, 2023: Fixed in [PR](https://github.com/aio-libs/aiohttp/pull/7713).
8. Some non-ASCII bytes are incorrectly permitted in header names.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\n\xefoo: bar\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - October 17, 2023: Reported via [PR](https://github.com/aio-libs/aiohttp/pull/7719).
      - October 18, 2023: Fixed via merge of above PR.
    - Daphne:
      - February 4, 2024: Reported via [GH issue](https://github.com/django/daphne/issues/497).
      - February 10, 2024: Fixed in [commit](https://github.com/django/daphne/commit/ef247962439eb19c52ae36e431307b98ed16b7f5).
    - Mongoose:
      - October 13, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2425).
      - December 5, 2023: Fixed in [commit](https://github.com/cesanta/mongoose/commit/bd53e4687377af2c7d56ce69e3af289e59654cb0).
9. `\n` is allowed as separating whitespace in a request line.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards HTTP/0.9 requests with bare `\n` as-is, and reuses the underlying connection.
  - Risk: Low. I'm not aware of any vulnerable transducers.
  - Payload: `GET /\nHTTP/1.1\r\n\r\n`
  - Affected programs:
    - AIOHTTP:
      - October 17, 2023: Reported via [PR](https://github.com/aio-libs/aiohttp/pull/7719).
      - October 18, 2023: Fixed via merge.
10. The Python `int` constructor is used to parse `Content-Length` values, so `_`, `+`, and `-` are misinterpreted.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets `Content-Length` values as their longest valid prefix, but forwards them as-is.
  - Risk: Low. I'm not aware of any vulnerable transducers, but Matt Grenfeldt [says that at least one exists](https://grenfeldt.dev/2021/10/08/gunicorn-20.1.0-public-disclosure-of-request-smuggling/).
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: +1_0\r\n\r\n0123456789`
  - Affected programs:
    - AIOHTTP:
      - August 1, 2023: Reported via [GH security advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-gfw2-4jvh-wgfg).
      - October 7, 2023: Fixed in [release 3.8.6](https://github.com/aio-libs/aiohttp/releases/tag/v3.8.6).
    - CPython http.server:
      - April 2, 2023: Reported via [GH issue](https://github.com/python/cpython/issues/103204).
      - April 2, 2023: Fixed in commits [cf720ac](https://github.com/python/cpython/commit/cf720acfcbd8c9c25a706a4b6df136465a803992) and [cf720ac](https://github.com/python/cpython/commit/b4c1ca29ccd45c608ff01ce0a4608b1837715573).
    - Tornado:
      - August 2, 2023: Reported via [GH security advisory](https://github.com/tornadoweb/tornado/security/advisories/GHSA-qppv-j76h-2rpx).
      - August 10, 2023: Fixed in [commit](https://github.com/tornadoweb/tornado/commit/b7a5dd29bb02950303ae96055082c12a1ea0a4fe).
    - Werkzeug:
      - June 1, 2023: Reported via [GH issue](https://github.com/pallets/werkzeug/issues/2716).
      - June 7, 2023: Fixed in [commit 88c5c78](https://github.com/pallets/werkzeug/commit/86c5c78adf0d58b3a0a18b719fe802a19ea78b2c).
11. Header names containing any of ``!#$%&'*+.^_`|~`` are incorrectly rejected.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTe!st: a\r\n\r\n`
  - Affected programs:
    - Bun:
      - October 12, 2023: Reported via [GH issue](https://github.com/oven-sh/bun/issues/6462).
      - January 31, 2024: Remains unfixed.
12. The connection is closed without an error response when a message containing no `Host` header is received.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\n\r\n`
  - Affected programs:
    - Bun:
      - February 2, 2024: Reported via [GH issue](https://github.com/oven-sh/bun/issues/8648).
      - February 2, 2024: Remains unfixed.
13. `\r` is treated as a line terminator in header field lines.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards `\r` in header names.
  - Risk: High. See transducer bug 10.
  - Payload: `GET / HTTP/1.1\r\nVisible: :/\rSmuggled: :)\r\n\r\n`
  - Affected programs:
    - CPython http.server:
      - January 31, 2024: Reported via [GH issue](https://github.com/python/cpython/issues/114782).
      - January 31, 2024: Remains unfixed.
    - Mongoose:
      - July 7, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2292).
      - July 9, 2023: Fixed in [commit 6957c37](https://github.com/cesanta/mongoose/commit/6957c379d5c43115e6b2f1206c0c7f24172f7044).
14. Disallowed ASCII characters are incorrectly permitted in header names.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\n\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f "(),/;<=>?@[/]{}: whatever\r\n\r\n`
  - Affected programs:
    - Daphne:
      - February 4, 2024: Reported via [GH issue](https://github.com/django/daphne/issues/497).
      - February 10, 2024: Fixed in [commit](https://github.com/django/daphne/commit/ef247962439eb19c52ae36e431307b98ed16b7f5).
    - Mongoose:
      - October 13, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2425).
      - December 5, 2023: Fixed in [commit](https://github.com/cesanta/mongoose/commit/bd53e4687377af2c7d56ce69e3af289e59654cb0).
    - Tornado:
      - August 11, 2023: Reported via [GH issue](https://github.com/tornadoweb/tornado/issues/3310).
      - January 31, 2024: Remains unfixed.
    OpenLiteSpeed:
      - July 31, 2023: Reported via email.
      - August 10, 2023: Fixed in OLS 1.7.18.
15. HTTP versions are not validated.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/\r\r1.1\r\n\r\n`
  - Affected programs:
    - FastHTTP:
      - February 4, 2024: Reported via [GH issue](https://github.com/valyala/fasthttp/issues/1703).
      - February 11, 2024: Fixed in [commit](https://github.com/valyala/fasthttp/commit/332726634240b82456ce8563cd7aa4027612ce36).
16. Empty `Content-Length` values are treated as though they were `0`.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets empty `Content-Length` values as anything other than 0.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length: \r\n\r\n`
  - Affected programs:
    - Go net/http:
      - July 31, 2023: Reported via [GH issue](https://github.com/golang/go/issues/61679)
      - August 11, 2023: Fixed in [commit](https://github.com/golang/go/commit/610d47a584e780f4af7978904c4c162de7ceee0b).
    - Lighttpd:
      - August 1, 2023: Reported via [issue tracker](https://redmine.lighttpd.net/issues/3219).
      - August 3, 2023: Fixed in [commit](https://redmine.lighttpd.net/projects/lighttpd/repository/14/revisions/d71fc70c8d45b7978f0226e6cdfe286fba34f1e7).
    - OpenLiteSpeed:
      - July 31, 2023: Reported via email.
      - August 10, 2023: Fixed in OLS 1.7.18.
17. Empty chunk-sizes are treated as though they were `0`.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards extra `\r\n`s between chunks.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n\r\n\r\n`
  - Affected programs:
    - Go net/http:
      - December 2, 2023: Reported via [GH issue](https://github.com/golang/go/issues/64517).
      - January 4, 2024: Fixed in [commit](https://github.com/golang/go/commit/ead47b0ab39c5819aee207cda536531a8e44ddc7).
    - Hyper:
      - December 1, 2023: Reported via email.
      - December 18, 2023: Fixed in [commit](https://github.com/hyperium/hyper/commit/829153865a4d2bbb52227183c8857e57dc3e231b).
    - Mongoose:
      - January 3, 2024: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2552).
      - January 3, 2024: Fixed in [PR](https://github.com/cesanta/mongoose/pull/2580).
18. Empty header names are erroneously accepted.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `\r\n:\r\n`, and treats it as the end of the header block.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\n: ignored\r\nHost: whatever\r\n\r\n`
  - Affected programs:
    - Go net/http:
      - January 24, 2024: Reported via [GH issue](https://github.com/golang/go/issues/65244).
      - January 30, 2024: Fixed in [commit](https://github.com/golang/go/commit/ae457e811d44261801bda261731b5006d629930d).
    - Gunicorn:
      - December 4, 2023: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3104).
      - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).
    - Node.js:
      - October 13, 2023: Reported via [GH issue](https://github.com/nodejs/llhttp/issues/257).
      - October 17, 2023: Fixed in [commit](https://github.com/nodejs/llhttp/commit/10ff94eb252e0e7cb792dcde6d40d0e46b794f8a).
    - Tornado:
      - October 13, 2023: Reported via [GH issue comment](https://github.com/tornadoweb/tornado/issues/3310#issuecomment-1761974522).
      - October 15, 2023: Remains unfixed.
19. All non-`\r\n` whitespace sequences are stripped from the beginnings of header values (after the `:`).
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards bare `\n` line endings in field lines.
  - Risk: Medium. See transducer bug 16.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nUseless:\n\nGET / HTTP/1.1\r\n\r\n`
  - Affected programs:
    - Gunicorn:
      - June 2, 2023: Reported via email.
      - January 31, 2024: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3144).
      - January 31, 2024: Remains unfixed.
20. `\xa0` and `\x85` bytes are stripped from the ends of header names, before the `:`.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards `\xa0` or `\x85`in header names.
  - Risk: Medium. See transducer bug 6.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length\x85: 10\r\n\r\n0123456789`
  - Affected programs:
    - Gunicorn:
      - June 27, 2023: Reported via email.
      - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).
21. `,chunked` is treated as an encoding distinct from `chunked`.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards the `Transfer-Encoding` value `,chunked` as-is, and interprets it as equivalent to `chunked`.
  - Risk: High. See transducer bug 9.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - Gunicorn:
      - November 6, 2023: Reported via [GH issue](https://github.com/benoitc/gunicorn/issues/3087).
      - December 25, 2023: Fixed in [commit](https://github.com/benoitc/gunicorn/commit/0b4c93952723d917d50de09d9c8e43e000a35ccd).
    - Mongoose:
      - November 6, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2460).
      - December 1, 2023: Fixed in [commit](https://github.com/cesanta/mongoose/pull/2509/commits/4c445453d354fe4ab21e59beae327d9e38832d93).
    - Passenger:
      - November 6, 2023: Reported via email.
      - January 22, 2024: Fixed in [release](https://github.com/phusion/passenger/releases/tag/release-6.0.20).
22. Invalid chunk-sizes are interpreted as their longest valid prefix.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards invalidly-prefixed chunk-sizes (e.g. with `0x` prefix).
  - Risk: High. See transducer bugs 2 and 19.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n0_2e\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - H2O:
      - August 1, 2023: Reported via email.
      - December 12, 2023: Fixed in [PR](https://github.com/h2o/picohttpparser/pull/78).
    - OpenLiteSpeed:
      - July 31, 2023: Reported via email.
      - August 10, 2023: Fixed in OLS 1.7.18.
    - WEBrick:
      - November 9, 2023: Reported via [GH issue](https://github.com/ruby/webrick/issues/124).
      - January 31, 2024: Remains unfixed.
23. Requests with multiple conflicting `Content-Length` headers are accepted, prioritizing the first.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards requests with 2 `Content-Length` headers, prioritizing the last.
  - Risk: Medium. See transducer bug 22.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: 1\r\nContent-Length: 0\r\n\r\nZ`
  - Affected programs:
    - H2O:
      - November 30, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
24. 8-bit integer overflow in HTTP version numbers.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/4294967295.255\r\n\r\n`
  - Affected programs:
    - Libevent:
      - January 17, 2024: Submitted [PR](https://github.com/libevent/libevent/pull/1541).
      - January 18, 2024: Fixed in merge.
25. Chunk-sizes are parsed using `strtoll(,,16)`, so `0x`, `+`, and `-` prefixes are erroneously accepted.
  - Use case: Request smuggling
  - Requirements: A transducer that interprets chunk-sizes as their longest valid prefix, but forwards them as-is.
  - Risk: Medium. See transducer bug 2.
  - Payload: `GET / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n`
  - Affected programs:
    - Libevent:
      - January 18, 2024: Submitted [PR](https://github.com/libevent/libevent/pull/1542).
      - February 18, 2024: Fixed in merge.
    - OpenLiteSpeed:
      - August 2, 2023: Reported via email.
      - August 11, 2023: Fixed in OLS 1.7.18.
26. Negative `Content-Length` headers can be used to force the server into an infinite busy loop.
  - Use case: DoS
  - Requirements: None.
  - Risk: High. This bug is trivial to exploit.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: -48\r\n\r\n`
  - Affected programs:
    - Mongoose:
      - April 27, 2023: Reported via email.
      - May 16-18, 2023: Fixed in commits [4663090](https://github.com/cesanta/mongoose/commit/4663090a8fb036146dfe77718cff612b0101cb0f), [926959a](https://github.com/cesanta/mongoose/commit/926959ab47e78302837bec864863d94dcb78a210), and [2669991](https://github.com/cesanta/mongoose/commit/26699914ccd4314903626afeb46621e066622fa0).
      - Assigned [CVE-2023-34188](https://www.cve.org/CVERecord?id=CVE-2023-34188).
27. The HTTP header block is truncated upon receipt of a header with no name or value.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards empty header names.
  - Risk: Medium. See bonus bonus bug 2.
  - Payload: `GET / HTTP/1.1\r\n:\r\nI: am chopped off\r\n\r\n`
  - Affected programs:
    - Mongoose:
      - June 26, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2275).
      - June 29, 2023: Fixed in [commit 415bbf2](https://github.com/cesanta/mongoose/commit/415bbf2932ba1da206aeefa7812621119ca70def).
28. Header names can be separated from values on space alone; no `:` required.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards header lines that don't contain a `:`.
  - Risk: Medium. See transducer bug 14.
  - Payload: `GET / HTTP/1.1\r\nContent-Length 10\r\n\r\n0123456789`
  - Affected programs:
    - Mongoose:
      - July 7, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2293).
      - July 7, 2023: Fixed in [commit 5dff282](https://github.com/cesanta/mongoose/commit/5dff2821325f445b971777e405eac732f7158a39).
29. Invalid `Content-Length` headers are interpreted as equivalent to their longest valid prefix.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards `Content-Length` values with invalid prefixes (e.g. `0x` or `+`)
  - Risk: High. See transducer bug 1.
  - Payload: `GET / HTTP/1.1\r\nContent-Length: 1Z\r\n\r\nZ`
  - Affected programs:
    - Mongoose:
      - July 31, 2023: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2322)
      - August 17, 2023: Fixed in [commit](https://github.com/cesanta/mongoose/commit/36fcb7ed210ce58715521f19aca5c566a5e6f58f).
    - OpenLiteSpeed:
      - July 31, 2023: Reported via email.
      - August 10, 2023: Fixed in OLS 1.7.18.
30. The header block can be incorrectly terminated on `\r\n\rX`, where `X` can be any byte.
  - Use case: ???
  - Requirements: A transducer that forwards header names beginning with `\r`, or allows `\r` as line-folding start-of-line whitespace.
  - Risk: Low. I'm not aware of such a transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\n\rZGET /evil: HTTP/1.1\r\nHost: a\r\n\r\n`
  - Affected programs:
    - Node.js:
      - July 7, 2023: Reported via [HackerOne report](https://hackerone.com/reports/2054283).
      - July 31, 2023: Fixed in [llhttp commit](https://github.com/nodejs/llhttp/commit/6d04465e8c98c57a17428bf7aa54cc9e0add30ff).
      - September 16, 2023: Fixed in [Node commit](https://github.com/nodejs/node/commit/e9ff81016dfcf183f4fcc2640497cb8b3365fdd7).
31. Chunk lines are incorrectly terminated on `\rX`, where `X` can be any byte.
  - Use case: Request smuggling.
  - Requirements: A transducer that forwards `\r` within the optional whitespace in a chunk-ext.
  - Risk: High. See transducer bug 3.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n5\r\r;ABCD\r\n34\r\nE\r\n0\r\n\r\nGET / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - Node.js:
      - July 9, 2023: Reported via [HackerOne comment](https://hackerone.com/reports/2054283).
      - July 31, 2023: Fixed in [llhttp commit](https://github.com/nodejs/llhttp/commit/6d04465e8c98c57a17428bf7aa54cc9e0add30ff).
      - September 16, 2023: Fixed in [Node commit](https://github.com/nodejs/node/commit/e9ff81016dfcf183f4fcc2640497cb8b3365fdd7).
32. `Content-Length` headers are interpreted with `strtoll(,,0)`, so leading `0`, `+`, `-`, and `0x` are misinterpreted.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards leading `0`s in `Content-Length` values, which is permitted by the standard.
  - Risk: High. This is exploitable against standards-compliant transducers.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nContent-Length: 010\r\n\r\n01234567`
  - Affected programs:
    - OpenLiteSpeed:
      - July 31, 2023: Reported via email.
      - August 10, 2023: Fixed in OLS 1.7.18.
33. Requests with multiple conflicting `Content-Length` headers are accepted, prioritizing the last.
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards requests with 2 `Content-Length` headers, prioritizing the first.
  - Risk: Low. I'm not aware of any such transducer, but the existence of one seems extremely likely.
  - Payload: `GET / HTTP/1.1\r\nHost: a\r\nContent-Length: 0\r\nContent-Length: 1\r\n\r\nZ`
  - Affected programs:
    - FastHTTP:
      - February 4, 2024: Reported via email.
      - February 11, 2024: Fixed in [commit](https://github.com/valyala/fasthttp/commit/bce576699a322ab33b618773a4456a25e602682d).
34. `\r` is permitted in header values.
  - Use case: ???
  - Requirements: A transducer that misinterprets and forwards `\r` in header values.
  - Risk: Low. I'm not aware of any such transducer.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nHeader: va\rlue\r\n\r\n`
  - Affected programs:
    - OpenLiteSpeed:
      - July 31, 2023: Reported via email.
      - August 10, 2023: Fixed in OLS 1.7.18.
35. Header values are truncated at `\x00`.
  - Use case: ACL bypass
  - Requirements: A transducer that forwards `\x00` in header values.
  - Risk: Medium. See transducer bug 12.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTest: test\x00THESE BYTES GET DROPPED\r\nConnection: close\r\n\r\n`
  - Affected programs:
    - OpenLiteSpeed:
      - November 3, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
36. Field-lines with no `:` are ignored.
  - Use case: ???
  - Requirements: A transducer that forwards field lines with no `:`.
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTest\r\nConnection: close\r\n\r\n`
  - Affected programs:
    - OpenLiteSpeed:
      - November 3, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
    - Nginx:
      - February 5, 202https://github.com/phusion/passenger/releases/tag/release-6.0.204: Remains unfixed.
37. Header names can be continued across lines.
  - Use case: request smuggling.
  - Requirements: A transducer that forwards header lines that don't contain a `:`.
  - Risk: Medium. See transducer bug 14.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-\r\nEncoding: chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - Passenger:
      - November 6, 2023: Reported via email.
      - January 22, 2024: Fixed in [release](https://github.com/phusion/passenger/releases/tag/release-6.0.20).
38. Empty `Content-Length` in requests are interpreted as ``read until timeout occurs."
  - Use case: Request smuggling
  - Requirements: A transducer that accepts and forwards empty `Content-Length` header values, and treats them as equivalent to 0.
  - Risk: Medium. See transducer bugs 5 and 11.
  - Payload: `GET / HTTP/1.1\r\nHost: localhost\r\nContent-Length: \r\n\r\nGET / HTTP/1.1\r\nHost: localhost\r\n\r\n`
  - Affected programs:
    - Puma:
      - June 16, 2023: Reported via email.
      - August 17, 2023: Fixed in Puma 6.3.1 and 5.6.7. See [advisory](https://github.com/puma/puma/security/advisories/GHSA-68xg-gqqm-vgj8).
39. Chunked message bodies are terminated on `\r\nXX`, where `XX` can be any two bytes.
  - Use case: Request smuggling
  - Requirements: A transducer that preserves trailer fields and does not add whitespace between the `:` and value within trailer fields. (ATS is one such server)
  - Risk: High. The requirements to exploit this bug do not require the transducer to violate the standards.
  - Payload: `GET / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n0\r\nX:POST / HTTP/1.1\r\n\r\n`
  - Affected programs:
    - Puma:
      - July 31, 2023: Reported via email.
      - August 17, 2023: Fixed in Puma 6.3.1 and 5.6.7. See [advisory](https://github.com/puma/puma/security/advisories/GHSA-68xg-gqqm-vgj8).
      - Assigned CVE-2023-40175.
40. HTTP methods and versions are not validated.
  - Use case: ???
  - Requirements: N/A
  - Risk: None.
  - Payload: `\x00 / HTTP/............0596.7407.\r\n\r\n`
  - Affected programs:
    - Waitress:
      - October 17, 2023: Submitted [PR](https://github.com/Pylons/waitress/pull/423).
      - February 4, 2024: Fixed in merge of PR.
41. `\xa0` and `\x85` are stripped from the beginnings and ends of header values, except for the `Transfer-Encoding` header.
  - Use case: Header value ACL bypass
  - Requirements: A transducer that accepts and forwards `\xa0` and `\x85` in place.
  - Risk: Medium. The standard allows transducers to forward obs-text in header values.
  - Payload: `GET /login HTTP/1.1\r\nHost: a\r\nUser: \x85admin\xa0\r\n\r\n`
  - Affected programs:
    - Waitress:
      - February 4, 2024: Reported via [GH issue](https://github.com/Pylons/waitress/issues/432).
      - February 4, 2024: Fixed in [commit](https://github.com/Pylons/waitress/commit/8565e0deaf0ffaea6c6f93e27e32b51f518ff05f).
42. Empty `Content-Length` values are interpreted as equivalent to `0`, and prioritized over any subsequent `Content-Length` values.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards empty `Content-Length` values before nonempty ones, and interprets the nonempty ones.
  - Risk: High. See transducer bug 11.
  - Payload: `GET / HTTP/1.1\r\nContent-Length: \r\nContent-Length: 43\r\n\r\nPOST /evil HTTP/1.1\r\nContent-Length: 18\r\n\r\nGET / HTTP/1.1\r\n\r\n`
  - Affected programs:
    - WEBrick:
      - August 14, 2023: Reported via [GH issue](https://github.com/ruby/webrick/issues/119).
      - August 15, 2023: Fixed in [PR](https://github.com/ruby/webrick/pull/120).
43. `\x00` is stripped from the ends of header values.
  - Use case: ACL bypass
  - Requirements: A transducer that forwards `\x00` in header values.
  - Risk: Medium. See transducer bug 12.
  - Payload: `GET / HTTP/1.1\r\nEvil: evil\x00\r\n\r\n`
  - Affected programs:
    - WEBrick:
      - November 30, 2023: Reported via [GH issue](https://github.com/ruby/webrick/issues/126).
      - January 31, 2024: Remains unfixed.
44. All unknown transfer codings are treated as equivalent to `chunked`.
  - Use case: Request smuggling
  - Requirements: A transducer that forwards Transfer-Encodings other than `identity` and `chunked`. This is allowed by the standard.
  - Risk: High. This allows for request smuggling against some standards-compliant transducers.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: blegh\r\n\r\n1\r\nZ\r\n0\r\n\r\n`
  - Affected programs:
    - FastHTTP:
      - February 4, 2024: Reported via email.
      - February 11, 2024: Fixed in [commit](https://github.com/valyala/fasthttp/commit/bce576699a322ab33b618773a4456a25e602682d).
45. Connections are closed prematurely when an invalid request is pipelined after a valid request.
  - Use case: ???
  - Requirements: None.
  - Risk: None.
  - Payload: `GET / HTTP/1.1\r\nConnection: close\r\n\r\nInvalid\r\n\r\n`
  - Affected programs:
    - Mongoose:
      - January 29, 2024: Reported via [GH issue](https://github.com/cesanta/mongoose/issues/2592).
      - February 13, 2024: Fixed in [commit](https://github.com/cesanta/mongoose/commit/2419f0276634dccf505967df1ca234bc3a68fb84).
    - Uvicorn:
      - January 29, 2024: Reported via [GH discussion comment](https://github.com/encode/uvicorn/discussions/2234).
      - February 6, 2024: Inadvertently fixed in [commit](https://github.com/encode/uvicorn/commit/2ff704b91c8a3888eae7bfc3b053168dc59bd66e).
46. Bytes greater than `\x80` are stripped from the beginnings and ends of header values.
  - Use case: Host of troubles.
  - Requirements: A transducer that forwards Host headers containing bytes greater than `\x80`.
  - Risk: Medium.
  - Payload: `POST / HTTP/1.1\r\nHost: \xffa\xff\r\nTransfer-Encoding: \xffchunked\xff\r\n\r\n1\r\nZ\r\n0\r\n\r\n`
  - Affected programs:
    - Bun:
      - February 13, 2024: Reported via [GH issue](https://github.com/oven-sh/bun/issues/8893).
      - February 13, 2024: Remains unfixed.
47. When an invalid chunk is received, the connection isn't closed, and the start of the next message is placed after the first `\r\n` following the invalid chunk.
  - Use case: Response queue poisoning.
  - Requirements: A transducer that forwards invalid chunks.
  - Risk: Medium.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\nINVALID!!!\r\nGET / HTTP/1.1\r\nHost: whatever\r\n\r\n`
  - Affected programs:
    - CherryPy:
      - February 14, 2024: Reported via [GH issue](https://github.com/cherrypy/cherrypy/issues/2018).
      - February 14, 2024: Remains unfixed.
48. Pipelined requests in the initial request buffer are interpreted as the message body of the first request in the buffer, even if it has a `Content-Length: 0` header.
  - Use case: Request smuggling
  - Requirements: A transducer that doesn't change incoming stream element boundaries.
  - Risk: Low. I am not aware of any such transducer
  - Payload: `POST / HTTP/1.1\r\nContent-Length: 0\r\nConnection:keep-alive\r\nHost: a\r\nid: 0\r\n\r\nPOST / HTTP/1.1\r\nHost: a\r\nid: 1\r\nContent-Length: 34\r\n\r\n` `GET / HTTP/1.1\r\nHost: a\r\nid: 2\r\n\r\n`
  - Affected programs:
    - Puma:
      - February 2, 2024: Reported via email.
      - February 2, 2024: Fixed in [commit](https://github.com/puma/puma/commit/fed488f635a9625a5d34f617db25d0f85c7b49ed).

## Transducer Bugs
These are bugs in the way transducers interpret, normalize, and forward requests.

1. `0x`-prefixed `Content-Length` values are incorrectly accepted and forwarded, without validation of the message body.
  - Use case: Request smuggling
  - Requirements: A server that either interprets `Content-Length` as its longest valid prefix, or interprets `0x`-prefixed `Content-Length`.
  - Risk: Medium. See servers bugs 10, 29, and 32.
  - Payload: `POST / HTTP/1.1\r\nHost: akamai.my-domain.cool\r\nContent-Length: 0x10\r\n\r\nZ`
  - Affected programs:
    - Akamai CDN:
      - September 7, 2023: Reported via email.
      - November 27, 2023: Notified of fix via email.
2. Invalid chunk-size values are incorrectly accepted and forwarded.
  - Use case: Request smuggling
  - Requirements: An HTTP/1.1 backend server
  - Risk: High. This bug was exploitable for request smuggling against arbitrary backends.
  - Payload: `POST / HTTP/1.1\r\nHost: akamai.my-domain.cool\r\nTransfer-Encoding: chunked\r\n\r\nZ\r\nZZ\r\nZZZ\r\n\r\n`
  - Affected programs:
    - Akamai CDN:
      - September 7, 2023: Reported via email.
      - November 27, 2023: Notified of fix via email.
3. `\r` is incorrectly permitted in chunk-ext whitespace before the `;`.
  - Use case: Request smuggling
  - Requirements: A server that misinterprets `\r` in this location.
  - Risk: High. See server bug 31.
  - Payload: `POST / HTTP/1.1\r\nHost: server.my-domain.cool\r\nTransfer-Encoding: chunked\r\n\r\n2\r\r;a\r\n02\r\n41\r\n0\r\n\r\nGET /bad_path/pwned HTTP/1.1\r\nHost: a\r\nContent-Length: 430\r\n\r\n0\r\n\r\nGET / HTTP/1.1\r\nHost: server.my-domain.cool\r\n\r\n`
  - Affected programs:
    - Akamai CDN:
      - September 7, 2023: Reported via email.
      - November 27, 2023: Notified of fix via email.
    - Apache Traffic Server:
      - September 20, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10477).
      - January 31, 2024: Remains unfixed.
    - Google Cloud Classic Application Load Balancer:
      - September 13, 2023: Reported via [Google IssueTracker](https://issuetracker.google.com/issues/300252322).
      - January 30, 2024: Fixed on or before this date.
4. Placeholder :)
5. Empty `Content-Length` headers are incorrectly forwarded.
  - Use case: Request smuggling
  - Requirements: A server that interprets empty `Content-Length` values as anything other than 0
  - Risk: Medium. See server bug 38.
  - Payload: `GET / HTTP/1.1\r\nhost: whatever\r\ncontent-length: \r\n\r\n`
  - Affected programs:
    - Apache Traffic Server:
      - August 2, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10137#issue-1833493999).
      - August 6, 2023: Fixed via [PR](https://github.com/apache/trafficserver/pull/10144).
6. Disallowed bytes are accepted and forwarded within header names.
  - Use case: Request smuggling
  - Requirements: A server that misinterprets these invalid bytes within header names.
  - Risk: Medium. See server bug 41.
  - Payload: `GET / HTTP/1.1\r\nHost: fanout\r\nHeader\x85: value\r\n\r\n`
  - Affected programs:
    - Apache Traffic Server:
      - June 29, 2023: Reported via email.
      - September 18, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10459).
      - January 31, 2024: Remains unfixed.
    - OpenBSD relayd:
      - November 10, 2023: Reported via email.
      - November 28, 2023: Patched in [commit](https://github.com/openbsd/src/commit/1c543edce21c8c1ee56ef648930b92ca57a28d4f).
7. Chunk-sizes are interpreted as their longest valid prefix, and re-emitted.
  - Use case: Request smuggling
  - Requirements: A server that interprets `0_` or `0x` prefixes on chunk-sizes.
  - Risk: High. See server bugs 1, and 25, and transducer bug 19.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1these-bytes-never-get-validated\r\nZ\r\n0\r\n\r\n`
  - Affected programs:
    - Apache Traffic Server:
      - October 10, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10580).
      - January 31, 2024: Remains unfixed.
8. Placeholder :)
9. `Transfer-Encoding: ,chunked` headers are forwarded intact, and interpreted as equivalent to `chunked`.
  - Use case: Request smuggling
  - Requirements: A server that both ignores unknown `Transfer-Encoding`s and treats `,chunked` as distinct from `chunked`.
  - Risk: High. See server bug 21.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: ,chunked\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - Azure CDN:
      - October 15, 2023: Reported via [MSRC vulnerability report](https://msrc.microsoft.com/report/vulnerability/VULN-110915).
      - November 29, 2023: Fixed on or before this date.
      - December 12, 2023: "this case does not meet the bar for servicing by MSRC as HTTP smuggling is not consider a vulnerability and we will be closing this case."
    - nghttpx:
      - October 14, 2023: Reported via email.
      - October 17, 2023: Fixed in [PR](https://github.com/nghttp2/nghttp2/pull/1973).
10. `\r` is incorrectly forwarded in header values.
  - Use case: Request smuggling
  - Requirements: A server that treats `\r` as equivalent to `\r\n` within header fields.
  - Risk: Medium. See server bug 13.
  - Payload: `GET / HTTP/1.1\r\nInvalid-Header: this\rvalue\ris\rinvalid\r\n\r\n`
  - Google Cloud Classic Application Load Balancer:
      - September 7, 2023: Reported via [Google IssueTracker](https://issuetracker.google.com/issues/299469787).
      - January 30, 2024: Fixed on or before this date.
11. Empty `Content-Length` headers are incorrectly forwarded, even in the presence of other `Content-Length` headers, as long as the empty `Content-Length` header comes first.
  - Use case: Request smuggling
  - Requirements: A server that interprets empty `Content-Length` values as 0 and accepts multiple `Content-Length` headers in incoming requests, prioritizing the first.
  - Risk: Medium. See server bug 42.
  - Payload: `GET / HTTP/1.1\r\nhost: whatever\r\ncontent-length: \r\ncontent-length: 59\r\n\r\nPOST /evil HTTP/1.1\r\nhost: whatever\r\ncontent-length: 34\r\n\r\nGET / HTTP/1.1\r\nhost: whatever\r\n\r\n`
  - Affected programs:
    - HAProxy:
      - August 2, 2023: Reported via [GH issue](https://github.com/haproxy/haproxy/issues/2237).
      - August 9, 2023: Fixed in [commit](https://github.com/haproxy/haproxy/commit/6492f1f29d738457ea9f382aca54537f35f9d856).
      - August 10, 2023: Assigned [CVE-2023-40225](https://www.cve.org/CVERecord?id=CVE-2023-40225).
12. `\x00` is forwarded in header values.
  - Use case: ACL bypass
  - Requirements: A server that truncates header values at `\x00`.
  - Risk: Medium. See server bugs 35 and 43, and transducer bug 20.
  - Payload: `GET / HTTP/1.1\r\nHost: google.com\x00.kallus.org\r\n\r\n`
  - Affected programs:
    - HAProxy:
      - September 19, 2023: Reported via email.
      - January 31, 2024: Fixed in [commit](https://github.com/haproxy/haproxy/commit/0d76a284b6abe90b7001284a5953f8f445c30ebe).
    - OpenLiteSpeed:
      - November 3, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
13. Bare `\n` is accepted as a chunk line terminator.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `GET / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\na\r\n0123456789\n0\r\n\r\n`
  - Affected programs:
    - HAProxy:
      - January 25, 2024: Reported via email.
      - January 30, 2024: Fixed in commmits [7b737da](https://github.com/haproxy/haproxy/commit/7b737da8258ebdd84e702a2d65cfd3c423f8e96d) and [4837e99](https://github.com/haproxy/haproxy/commit/4837e998920cbd4e43026e0a638b8ebd71c8018f).
14. Field lines with no `:` are forwarded as-is.
  - Use case: Request smuggling
  - Requirements: A backend server that misinterprets header field lines with no `:`.
  - Risk: Medium. See transducer bugs 28 and 37.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTe\nst: test\r\nConnection: close\r\n\r\n`
  - Affected programs:
    - OpenLiteSpeed:
      - November 3, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
15. Requests containing both `Content-Length` and `Transfer-Encoding` headers are forwarded as-is if the `Transfer-Encoding` value is unrecognized.
  - Use case: Request smuggling
  - Requirements: A backend server that treats `,chunked` as equivalent to `chunked`, and prioritizes `Transfer-Encoding` over `Content-Length`. These behaviors are allowed by the standards.
  - Risk: High. This allows request smuggling to standards-compliant servers.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\nConnection: close\r\n\r\n0r\n\r\n`
  - Affected programs:
    - OpenLiteSpeed:
      - November 3, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
    - Pound:
      - February 4, 2024: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/26).
      - February 4, 2024: Remains unfixed.
16. `\n` is not normalized to `\r\n` in forwarded messages.
  - Use case: Request smuggling
  - Requirements: A backend server that does not interpret `\n` as a line ending in header lines. The standard allows servers to translate `\n` to ` `.
  - Risk: High. This bug is exploitable against standards-compliant servers.
  - Payload: `GET / HTTP/1.1\nHost: whatever\nConnection: close\n\n`
  - Affected programs:
    - OpenLiteSpeed:
      - November 3, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
17. Chunked message bodies containing an extra `\r\n` before the terminator chunk are un-chunked without replacing the `Transfer-Encoding` header with `Content-Length`.
  - Use case: Request smuggling
  - Requirements: None.
  - Risk: High. This bug is exploitable against arbitrary backend servers.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n17\r\n0\r\n\r\nGET / HTTP/1.1\r\n\r\n\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - OpenLiteSpeed
      - November 30, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
18. `Transfer-Encoding: ,chunked` headers are forwarded intact, and are not interpreted as equivalent to `chunked`.
  - Use case: Request smuggling
  - Requirements: A server that interprets `,chunked` as equivalent to `chunked`, which the standard says you MAY do.
  - Risk: High. This is a request smuggling vulnerability that is usable against standards-compliant backends.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: ,chunked\r\nContent-Length: 5\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - OpenBSD relayd:
      - November 10, 2023: Reported via email.
      - November 28, 2023: Patched in [commit](https://github.com/openbsd/src/commit/1c543edce21c8c1ee56ef648930b92ca57a28d4f).
19. Chunk-sizes with `+`, `-`, and `0x` prefixes are interpreted and forwarded.
  - Use case: Request smuggling
  - Requirements: A server that interprets chunk sizes as their longest valid prefix.
  - Risk: High. See server bug 22.
  - Payload: `POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n-0x0\r\n\r\n`
  - Affected programs:
    - OpenBSD relayd:
      - November 10, 2023: Reported via email.
      - November 28, 2023: Patched in [commit](https://github.com/openbsd/src/commit/1c543edce21c8c1ee56ef648930b92ca57a28d4f).
    - Pound:
      - October 10, 2023: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/19).
      - October 11, 2023: Fixed via commits [60a4f42](https://github.com/graygnuorg/pound/commit/60a4f42b2a1f901aec9746cde56c2f19a4a1a332) and [f70db92](https://github.com/graygnuorg/pound/commit/f70db92c126fffaab62b1f003413d8bdd93e45b0).
20. Headers containing `\x00` or `\n` are concatenated into the previous header's value.
  - Use case: Request smuggling
  - Requirements: Any standards-compliant backend server.
  - Risk: High. This is a generic request smuggling vulnerability.
  - Payload: `GET / HTTP/1.1\r\na:b\r\nc\x00\r\n\r\n`
  - Affected programs:
    - OpenBSD relayd:
      - November 10, 2023: Reported via email.
      - November 29, 2023: Patched in [commit](https://github.com/openbsd/src/commit/eefb3de5799409f8689b849d8a069ad293a002c0).
21. Message bodies are stripped from `GET` requests without removing their `Content-Length` headers.
  - Use case: Request smuggling
  - Requirements: Any backend server that supports pipelining.
  - Risk: High. This is a generic request smuggling vulnerability.
  - Payload: `GET / HTTP/1.1\r\nContent-Length: 10\r\n\r\n1234567890`
  - Affected programs:
    - OpenBSD relayd:
      - November 28, 2023: Reported via email.
      - December 1, 2023: Patched in [commit](https://github.com/openbsd/src/commit/f537694384c3e3ea254eafa0a11f77c5c3e9c1a2).
22. Requests containing multiple `Content-Length` headers are forwarded, prioritizing the last.
  - Use case: Request smuggling
  - Requirements: A server that accepts requests containing multiple `Content-Length` headers, prioritizing the first.
  - Risk: High. See server bug 23.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: 0\r\nContent-Length: 31\r\n\r\nGET /evil HTTP/1.1\r\nHost: a\r\n\r\n`
  - Affected programs:
    - OpenBSD relayd:
      - November 30, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
23. Requests containing both `Content-Length` and `Transfer-Encoding` are forwarded.
  - Use case: Request smuggling
  - Requirements: A server that prioritizes `Content-Length` over `Transfer-Encoding`, or does not support `Transfer-Encoding: chunked`.
  - Risk: High. This is the classic request smuggling vector.
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nContent-Length: 5\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - OpenBSD relayd:
      - November 30, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
24. Whitespace-prefixed chunk-sizes are accepted and forwarded.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n           0\r\n\r\n`
  - Affected programs:
    - OpenBSD relayd:
      - November 30, 2023: Reported via email.
      - January 31, 2024: Remains unfixed.
    - Pound:
      - October 15, 2023: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/20).
      - November 25, 2023: Fixed in [commit](https://github.com/graygnuorg/pound/commit/387013528023bb0f2950959d15f5ae538ac23737).
28. Requests containing multiple `Transfer-Encoding: chunked` headers are forwarded, and treated as equivalent to a single such header.
  - Use case: Request smuggling
  - Requirements: A server that treats multiple `Transfer-Encoding: chunked` headers as not equivalent to no `Transfer-Encoding: chunked`, or joins multiple `Transfer-Encoding` headers, and treats `chunked,chunked` as distinct from `chunked`.
  - Risk: Medium. See server bug 21.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n`
  - Affected programs:
    - Pound:
      - October 7, 2023: Reported via [GH issue](https://github.com/graygnuorg/pound/issues/18).
      - October 12, 2023: Fixed in [commit](https://github.com/graygnuorg/pound/commit/8d86d52d0bc65534c33018b0a01996081d23b89e).

## Redacted bugs
These are bugs about which we have decided not to release the details yet.

1. REDACTED
  - Use case: REDACTED
  - Requirements: REDACTED
  - Risk: Medium. REDACTED
  - Payload: REDACTED
  - Affected programs:
    - Libevent:
      - January 29, 2024: Reported via [GH security advisory](https://github.com/libevent/libevent/security/advisories/GHSA-g8g4-m98c-cwgh).
      - January 31, 2024: Remains unfixed.
2. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: High. REDACTED
  - Payload: REDACTED
  - Affected programs:
    - Tornado:
      - October 7, 2023: Reported via [GH security advisory](https://github.com/tornadoweb/tornado/security/advisories/GHSA-753j-mpmx-qq6g).
      - January 31, 2024: Remains unfixed.
3. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: Medium. REDACTED
  - Payload: REDACTED
  - Affected programs:
    - Tornado:
      - February 4, 2024: Reported via [GH security advisory comment](https://github.com/tornadoweb/tornado/security/advisories/GHSA-753j-mpmx-qq6g#advisory-comment-95237).
      - February 4, 2024: Remains unfixed.
4. REDACTED
  - Use case: Request smuggling
  - Requirements: REDACTED
  - Risk: High. REDACTED
  - Payload: REDACTED
  - Affected programs:
    - Akamai CDN:
      - December 3, 2023: Reported via email.
      - January 30, 2024: Remains unfixed.

## Bonus bugs
These are bugs we found incidentally just by setting up the HTTP Garden and sending an example request. They don't really count because they didn't require using the Garden, but I figure I should document them anyway.

1. NULL argument passed to `memcpy` in triggers undefined behavior.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: Any request with an empty message body that will be forwarded to a proxy_fcgi backend.
  - Affected programs:
    - Apache httpd:
      - December 2, 2023: Reported via [Bugzilla issue](https://bz.apache.org/bugzilla/show_bug.cgi?id=68278).
      - December 19, 2023: Fixed in [revision 1914775](https://svn.apache.org/viewvc?view=revision&revision=1914775).
    - uwsgi:
      - January 1, 2024: Reported via [GH issue](https://github.com/unbit/uwsgi/issues/2596).
      - Februiary 8, 2024: Patched in [PR](https://github.com/unbit/uwsgi/pull/2597).
2. Use-after-free.
  - Use case: DoS
  - Requirements: The server uses `attach_server_session_to_client`
  - Risk: Low. While this does crash ATS, it's so easy to notice that a reasonable person would not have deployed a vulnerable instance in production.
  - Payload: Any request at all.
  - Affected programs:
    - Apache Traffic Server:
      - July 31, 2023: Reported via [GH issue](https://github.com/apache/trafficserver/issues/10116).
      - September 13, 2023: Fixed via [PR](https://github.com/apache/trafficserver/pull/10399).
3. Sending an extra byte after a request with a chunked message body crashes the server with a segfault.
  - Use case: DoS
  - Requirements: FastCGI is enabled.
  - Risk: High. This is a trivial-to-exploit bug that crashes the server.
  - Payload: `GET / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n\x00`
  - Affected programs:
    - OpenBSD httpd:
      - November 1, 2023: Reported via email.
      - November 8, 2023: Fixed in [commit](https://github.com/openbsd/src/commit/76ed904538b7966e735c4736a6e2cf7222ad67cf).
4. Incoming chunked request bodies are echoed back before the response is sent.
  - Use case: DoS
  - Requirements: FastCGI is enabled.
  - Risk: Medium. This will invalidate the request stream for any chunked message, which will ruin shared connections.
  - Payload: `POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\rn\`
  - Affected programs:
    - OpenBSD httpd:
      - January 4, 2024: Reported via email.
      - January 31, 2024: Remains unfixed.
5. NULL dereference upon receipt of any request.
  - Use case: DoS
  - Requirements: `mod_dir` is enabled with certain configuration options.
  - Risk: Low. This bug is so obvious that no one sane would deploy a vulnerable server.
  - Payload: Anything at all.
  - Affected programs:
    - Apache httpd:
      - January 24, 2024: Reported via [Bugzilla issue](https://bz.apache.org/bugzilla/show_bug.cgi?id=68527).
      - January 24, 2024: Remains unfixed.

## Bonus Bonus Bugs
These are bugs that we found back when the Garden had HTTP/2 support. We removed HTTP/2 support because it was a little half-baked, but would love to be able to add it back!
1. Whitespace characters are not stripped from field values during HTTP/2 to HTTP/1.1 downgrades.
  - Use case: ???
  - Requirements: N/A
  - Risk: None
  - Payload: `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00E\x01\x05\x00\x00\x00\x01\x00\n:authority\tlocalhost\x00\x05:path\x01/\x00\x07:method\x03GET\x00\x07:scheme\x04http\x00\x05test1\x03\ta\t`
  - Affected programs:
    - Envoy:
      - July 7, 2023: Reported via [GH issue](https://github.com/envoyproxy/envoy/issues/28285).
      - October 7, 2023: Remains unfixed.
    - H2O:
      - July 7, 2023: Reported via [GH issue](https://github.com/h2o/h2o/issues/3250).
      - July 18, 2023: Fixed in [PR #3256](https://github.com/h2o/h2o/pull/3256).
    - Varnish Cache:
      - July 7, 2023: Reported via [GH issue](https://github.com/varnishcache/varnish-cache/issues/3952).
      - August 22, 2023: Fixed in [commit](https://github.com/varnishcache/varnish-cache/commit/6af7d972d30371154d9b86943258905e58748ce5).
2. Empty header names are preserved across HTTP/2 to HTTP/1.1 translation, leading to the production of invalid HTTP/1.1.
  - Use case: DoS
  - Requirements: An HTTP/2 downgrade is being performed, and the backend rejects empty header names (as most do).
  - Risk: Low. This bug can be used to make a reasonable server 400, which will break connection sharing.
  - Payload: `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00=\x01\x05\x00\x00\x00\x01\x00\n:authority\tlocalhost\x00\x05:path\x01/\x00\x07:method\x03GET\x00\x07:scheme\x04http\x00\x00\x00`
  - Affected programs:
    - H2O:
      - July 7, 2023: Reported via [GH issue](https://github.com/h2o/h2o/issues/3250).
      - July 18, 2023: Fixed in [PR #3256](https://github.com/h2o/h2o/pull/3256).
