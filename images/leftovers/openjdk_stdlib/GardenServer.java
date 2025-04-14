import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.net.InetSocketAddress;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Base64;
import java.lang.StringBuilder;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.io.ByteArrayOutputStream;
import java.util.Arrays;
import java.util.Map;
import java.util.List;

class GardenServer {
    private static String base64_encode(String s) {
        try {
            return Base64.getEncoder().encodeToString(s.getBytes("ISO-8859-1"));
        } catch (UnsupportedEncodingException e) {
            return "This should never happen.";
        }
    }

    private static String base64_encode(byte[] s) {
        return Base64.getEncoder().encodeToString(s);
    }

    private static byte[] read_input_stream(InputStream is) throws IOException {
        ByteArrayOutputStream os = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        while (true) {
            int read = is.read(buf);
            if (read == -1) {
                break;
            }
            os.write(Arrays.copyOfRange(buf, 0, read));
        }
        return os.toByteArray();
    }

    private static class GardenHandler implements HttpHandler {
        public void handle(HttpExchange exch) throws IOException {
            StringBuilder response_builder = new StringBuilder("{\"version\":\"")
                .append(base64_encode(exch.getProtocol()))
                .append("\",\"method\":\"")
                .append(base64_encode(exch.getRequestMethod()))
                .append("\",\"uri\":\"")
                .append(base64_encode(exch.getRequestURI().toString()))
                .append("\",\"headers\":[");
            boolean first = true;
            for (Map.Entry<String, List<String>> h: exch.getRequestHeaders().entrySet()) {
                for (String v : h.getValue()) {
                    if (!first) {
                        response_builder.append(",");
                    }
                    response_builder
                        .append("[\"")
                        .append(base64_encode(h.getKey()))
                        .append("\",\"")
                        .append(base64_encode(v))
                        .append("\"]");
                    first = false;
                }
            }

            response_builder.append("],\"body\":\"")
                .append(base64_encode(read_input_stream(exch.getRequestBody())))
                .append("\"}");
            String response_body = response_builder.toString();
            exch.sendResponseHeaders(200, response_body.length());
            OutputStream os = exch.getResponseBody();
            os.write(response_body.getBytes("ISO-8859-1"));
            os.close();
        }
    }

    public static void main(String[] _unused) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", 80), 0);
        server.createContext("/", new GardenHandler());
        server.setExecutor(null);
        server.start();
    }
}
