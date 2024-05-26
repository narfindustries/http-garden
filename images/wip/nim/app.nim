# Based on the example program at https://nim-lang.org/docs/asynchttpserver.html

import std/asynchttpserver
import std/asyncdispatch
import std/base64
import std/tables

proc main {.async.} =
  var server = newAsyncHttpServer()
  proc cb(req: Request) {.async.} =
    var uri = req.url
    var result = "{\"headers\":["
    var first = true
    for key, seq in req.headers.table:
      for val in seq:
        if not first:
          result &= ","
        first = false
        result &= "[\""
        result &= encode(key)
        result &= "\",\""
        result &= encode(val)
        result &= "\"]"
    result &= "],\"method\":\""
    result &= encode(req.reqMethod.repr)
    result &= ",\"uri\":\""
    result &= encode($uri)
    result &= "\",\"version\":"
    result &= encode(req.protocol.orig)
    result &= "\",\"body\":\""
    result &= encode(req.body)
    result &= "\"}"
    await req.respond(Http200, result, newHttpHeaders())

  server.listen(Port(80))
  while true:
    await server.acceptRequest(cb)

waitFor main()
