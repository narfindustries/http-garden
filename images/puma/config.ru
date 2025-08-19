require 'json'
require 'base64'

class Server
  def call(env) 
    result = {}
    result['headers'] = []
    env.each do |key, value|
      if not ["rack.tempfiles", "rack.request.form_hash", "rack.request.form_vars", "rack.request.form_input", "rack.version","rack.errors","rack.multithread","rack.multiprocess","rack.run_once","rack.url_scheme","SCRIPT_NAME","QUERY_STRING","SERVER_SOFTWARE","GATEWAY_INTERFACE","REQUEST_METHOD","REQUEST_PATH","REQUEST_URI","SERVER_PROTOCOL","puma.request_body_wait","SERVER_NAME","SERVER_PORT","PATH_INFO","REMOTE_ADDR","HTTP_VERSION","puma.socket","rack.hijack?","rack.hijack","rack.input","rack.after_reply","puma.config","rack.logger","rack.request.query_string","rack.request.query_hash","sinatra.route", "rack.response_finished"].include?(key)
      # Note: Puma is blind to any headers with name.lower() == "version" because of the builtin HTTP_VERSION environment variable
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
