local base64 = require 'base64'

function handle_request(env)
    result = "{\"headers\":["
    first = true
    for k, v in pairs(env.headers) do
        if k ~= "URL" then
            if first then
                first = false
            else
                result = result .. ","
            end
            result = result .. "[\"" .. base64.encode(k) .. "\",\"" .. base64.encode(v) .. "\"]"
        end
    end
    result = result .. "],"
    result = result .. "\"uri\":\"" .. base64.encode(env.REQUEST_URI) .. "\","
    result = result .. "\"version\":\"" .. base64.encode(tostring(env.HTTP_VERSION)) .. "\","
    result = result .. "\"body\":\"" .. base64.encode(io.read("*all")) .. "\","
    result = result .. "\"method\":\"" .. base64.encode(env.REQUEST_METHOD) .. "\"}"

    uhttpd.send("Status: 200 OK\r\n")
    uhttpd.send("Content-Type: application/json\r\n\r\n");
    uhttpd.send(result)
end
