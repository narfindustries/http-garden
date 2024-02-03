require 'json'
require 'base64'

class Server
  def call(env) 
    result = {}
    result['headers'] = []
    env.each do |key, value|
      if not ["GATEWAY_INTERFACE", "PATH_INFO", "QUERY_STRING", "REMOTE_ADDR", "REMOTE_HOST", "REQUEST_METHOD", "REQUEST_URI", "SCRIPT_NAME", "SERVER_NAME", "SERVER_PORT", "SERVER_PROTOCOL", "SERVER_SOFTWARE", "rack.version", "rack.input", "rack.errors", "rack.multithread", "rack.multiprocess", "rack.run_once", "rack.url_scheme", "rack.hijack?", "rack.hijack", "rack.hijack_io", "HTTP_VERSION", "REQUEST_PATH", "rack.tempfiles"].include?(key)
        result['headers'].push([Base64.encode64(key.sub(/\AHTTP_/, "")).strip(), Base64.encode64(value).strip()])
      end
    end
    result['method'] = Base64.encode64(env["REQUEST_METHOD"]).strip()
    result['version'] = Base64.encode64(env["SERVER_PROTOCOL"]).strip()
    result['uri'] = Base64.encode64(env["REQUEST_PATH"] + (env["QUERY_STRING"] != "" ? ("?" + env["QUERY_STRING"]) : "")).strip()
    result['body'] = Base64.encode64(env["rack.input"].read).strip()
    [200, {}, [result.to_json]]
  end
end

run Server.new
