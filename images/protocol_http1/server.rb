# frozen_string_literal: true

require 'base64'
require 'json'
require 'socket'
require 'protocol/http1/connection'
require 'protocol/http/body/buffered'

def handle_connection(connection)
  loop do
    request = connection.read_request
    break unless request

    authority, method, path, version, headers, body_reader = request
    begin
      body = body_reader ? body_reader.join : ''
    rescue NoMethodError # This is a hack to work around [this bug](https://github.com/socketry/protocol-http1/issues/34).
      break # Once that bug is fixed, this code should be removed.
    end
    b64_headers = headers.fields.map do |k, v|
      [Base64.encode64(k).strip, Base64.encode64(v).strip]
    end
    b64_headers += [[Base64.encode64('Host').strip, Base64.encode64(authority).strip]] if authority
    result = {
      'headers': b64_headers,
      'method': Base64.encode64(method).strip,
      'uri': Base64.encode64(path).strip,
      'version': Base64.encode64(version).strip,
      'body': Base64.encode64(body).strip
    }

    connection.write_response(version, 200, [])
    connection.write_body(version, Protocol::HTTP::Body::Buffered.wrap([result.to_json]))

    break unless connection.persistent
  rescue Protocol::HTTP1::InvalidRequest, Protocol::HTTP1::BadRequest, Protocol::HTTP1::BadHeader
    break
  end
end

Addrinfo.tcp('0.0.0.0', 80).listen do |server|
  loop do
    client, _address = server.accept
    connection = Protocol::HTTP1::Connection.new(client)
    handle_connection(connection)
  end
end
