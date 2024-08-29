package com.example

import kotlin.io.encoding.Base64

import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.server.request.*
import io.ktor.server.engine.*
import io.ktor.server.cio.*
import io.ktor.http.*

fun main(args: Array<String>) {
    embeddedServer(CIO, port = 80) {
        routing {
            route("/{...}") {
                handle {
                    call.respondText(generate_response_body(call), ContentType.Application.OctetStream)
                }
            }
        }
    }.start(wait = true)
}

@OptIn(kotlin.io.encoding.ExperimentalEncodingApi::class)
suspend fun generate_response_body(call: RoutingCall): String {
    var result: String = "{"

    // headers
    result += "\"headers\":["
    var first: Boolean = true
    for (header in call.request.headers.entries()) {
        if (!first) {
            result += ","
        }
        first = false
        result += "[\"" + Base64.encode(header.key.toByteArray(Charsets.ISO_8859_1)) + "\",\"" + Base64.encode(header.value.joinToString(",").toByteArray(Charsets.ISO_8859_1)) + "\"]"
    }
    result += "],"

    // uri
    result += "\"uri\":\"" + Base64.encode(call.request.uri.toByteArray(Charsets.ISO_8859_1)) + "\","

    // version (hardcoded for now)
    result += "\"version\":\"SFRUUC8xLjE=\","

    // method
    result += "\"method\":\"" + Base64.encode(call.request.httpMethod.value.toByteArray(Charsets.ISO_8859_1)) + "\","

    // body
    result += "\"body\":\"" + Base64.encode(call.receive<ByteArray>()) + "\""

    result += "}"
    return result
}
