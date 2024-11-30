require 'json'
require 'base64'

class Server
  def call(env)
    result = {}
    result['headers'] = []
    env.each do |key, value|
      if not ["QUERY_STRING", "REQUEST_METHOD", "REQUEST_PATH", "PATH_INFO", "REQUEST_URI", "SERVER_PROTOCOL", "HTTP_VERSION", "rack.url_scheme", "SERVER_NAME", "SERVER_PORT", "REMOTE_ADDR", "rack.hijack", "rack.input", "rack.errors", "rack.multiprocess", "rack.multithread", "rack.run_once", "rack.hijack?", "rack.version", "SCRIPT_NAME", "SERVER_SOFTWARE", "rack.logger", "rack.tempfiles"].include?(key)
        result['headers'].push([Base64.encode64(key.sub(/\AHTTP_/, "")).strip(), Base64.encode64(value).strip()])
      end
    end
    result['method'] = Base64.encode64(env["REQUEST_METHOD"]).strip()
    result['uri'] = Base64.encode64(env["REQUEST_URI"]).strip()
    result['body'] = Base64.encode64(env["rack.input"].read).strip()
    result['version'] = Base64.encode64(env["SERVER_PROTOCOL"]).strip()
    [200, {}, [result.to_json]]
  end
end

run Server.new
