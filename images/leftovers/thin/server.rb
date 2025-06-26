require 'sinatra/base'
require 'rack/handler/thin'
require 'json'
require 'base64'

class App < Sinatra::Base
  def respond
    result = {}
    result['headers'] = []
    request.env.each do |key, value|
      if not ["rack.request.form_hash", "rack.tempfiles", "rack.request.form_vars", "rack.request.form_input", "SERVER_SOFTWARE", "SERVER_NAME", "rack.input", "rack.version", "rack.errors", "rack.multithread", "rack.multiprocess", "rack.run_once", "REQUEST_METHOD", "REQUEST_PATH", "PATH_INFO", "REQUEST_URI", "HTTP_VERSION", "GATEWAY_INTERFACE", "QUERY_STRING", "SERVER_PROTOCOL", "rack.url_scheme", "SCRIPT_NAME", "REMOTE_ADDR", "async.callback", "async.close", "rack.request.query_string", "rack.request.query_hash", "sinatra.route", "rack.logger", "SERVER_PORT"].include?(key)
        result['headers'].push([Base64.encode64(key.sub(/\AHTTP_/, "")).strip(), Base64.encode64(value).strip()])
      end
    end
    result['method'] = Base64.encode64(request.env["REQUEST_METHOD"]).strip()
    result['uri'] = Base64.encode64(request.env["REQUEST_PATH"] + (request.env["QUERY_STRING"] != "" ? ("?" + request.env["QUERY_STRING"]) : "")).strip()
    result['version'] = Base64.encode64(request.env["SERVER_PROTOCOL"]).strip()
    if request.body.is_a?(Tempfile)
      body_str = request.body.read
    else
      body_str = request.body.string
    end
    result['body'] = Base64.encode64(body_str).strip()
    result.to_json
  end

  delete '*' do
    respond
  end

  get '*' do
    respond
  end

  head '*' do
    respond
  end

  options '*' do
    respond
  end

  post '*' do
    respond
  end

  put '*' do
    respond
  end
end

Rack::Handler::Thin.run(App.new, Port: 80, Host: "0.0.0.0")
