require 'webrick'
require 'json'
require 'base64'

server = WEBrick::HTTPServer.new({:Port => 80})

server.mount_proc '/' do |request, response|
  result = {}
  result['headers'] = []
  if request.header != nil then
    request.header.each do |key, value|
      result['headers'].push([Base64.encode64(key).strip(), Base64.encode64(value.join(",")).strip()])
    end
  end
  result['version'] = Base64.encode64(request.http_version.to_s()).strip()
  result['method'] = Base64.encode64(request.request_method).strip()
  result['uri'] = Base64.encode64(request.unparsed_uri).strip()
  result['body'] = request.body().nil? ? "" : Base64.encode64(request.body()).strip()
  response.body = result.to_json
  response.status = 200
end

server.start()
