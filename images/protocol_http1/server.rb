#!/usr/bin/env ruby

require 'base64'
require 'json'
require 'socket'
require 'protocol/http1/connection'
require 'protocol/http/body/buffered'

Addrinfo.tcp("0.0.0.0", 80).listen do |server|
    loop do
        client, address = server.accept
        connection = Protocol::HTTP1::Connection.new(client)

        # Read request:
        while request = connection.read_request()
            authority, method, path, version, headers, body_reader = request
            body = body_reader.join()
            result = {
                'headers': headers.fields.map {
                    |k, v|
                    [Base64.encode64(k).strip(), Base64.encode64(v).strip()]
                } + (
                    authority ?
                    [[Base64.encode64("Host").strip(), Base64.encode64(authority).strip()]] :
                    []
                ),
                'method': Base64.encode64(method).strip(),
                'uri': Base64.encode64(path).strip(),
                'version': Base64.encode64(version).strip(),
                'body': (
                    body ?
                    Base64.encode64(body).strip() :
                    ""
                )
            }

            connection.write_response(version, 200, [])
            connection.write_body(version, Protocol::HTTP::Body::Buffered.wrap([result.to_json]))

            break unless connection.persistent
        end
    end
end
