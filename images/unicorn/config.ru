require 'json'
require 'base64'

class Server
  def call(env)
    result = {}
    result['headers'] = []
    env.each do |key, value|
      if not ["REMOTE_ADDR", "REQUEST_METHOD", "REQUEST_PATH", "PATH_INFO", "REQUEST_URI", "SERVER_PROTOCOL", "HTTP_VERSION", "rack.url_scheme", "SERVER_NAME", "SERVER_PORT", "QUERY_STRING", "rack.input", "unicorn.socket", "rack.hijack", "rack.errors", "rack.multiprocess", "rack.multithread", "rack.run_once", "rack.version", "rack.hijack?", "SCRIPT_NAME", "SERVER_SOFTWARE", "rack.logger", "rack.after_reply", "rack.tempfiles", "rack.lint"].include?(key)
        result['headers'].push([Base64.encode64(key.sub(/\AHTTP_/, "")).strip(), Base64.encode64(value).strip()])
      end
    end
    result['method'] = Base64.encode64(env["REQUEST_METHOD"]).strip()
    result['uri'] = Base64.encode64(env["REQUEST_PATH"] + (env["QUERY_STRING"] != "" ? ("?" + env["QUERY_STRING"]) : "")).strip()
    result['body'] = Base64.encode64(env["rack.input"].read).strip()
    result['version'] = Base64.encode64(env["SERVER_PROTOCOL"]).strip()
    [200, {}, [result.to_json]]
  end
end

run Server.new
