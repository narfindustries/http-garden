require 'json'
require 'base64'
require 'webrick'

server = WEBrick::HTTPServer.new(Port: 80)
server.mount_proc '/' do | req, res |
  result = {}
  result['headers'] = []
  req.header.each do |key, values|
    values.each do | value |
      result['headers'].push([Base64.encode64(key).strip(), Base64.encode64(value).strip()])
    end
  end
  result['method'] = Base64.encode64(req.request_method).strip()
  result['version'] = Base64.encode64(req.http_version.to_s).strip()
  result['uri'] = Base64.encode64(req.unparsed_uri).strip()
  if req.body and not req.body.empty?
    result['body'] = Base64.encode64(req.body).strip()
  else
    result['body'] = ""
  end
  res.body = result.to_json
end
server.start
