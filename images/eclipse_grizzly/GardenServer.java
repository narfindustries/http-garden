import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.io.ByteArrayOutputStream;
import java.lang.Thread;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

import org.glassfish.grizzly.http.server.HttpHandler;
import org.glassfish.grizzly.http.server.HttpServer;
import org.glassfish.grizzly.http.server.Request;
import org.glassfish.grizzly.http.server.Response;

public class GardenServer {
    private static String base64_encode(byte[] input) {
        return Base64.getEncoder().encodeToString(input);
    }

    public static void main(String[] args) throws IOException {
        final HttpServer server = HttpServer.createSimpleServer();
        for (HttpHandler handler: server.getServerConfiguration().getHttpHandlers().keySet()) {
            server.getServerConfiguration().removeHttpHandler(handler);
        }
        server.getServerConfiguration().addHttpHandler(new GardenHandler());
        server.start();
        while (true) {}
    }

    private static class GardenHandler extends HttpHandler {
        @Override
        public void service(Request request, Response response) throws IOException {
            final Reader in = request.getReader();
            final Writer out = response.getWriter();

            out.write("{\"method\":\"");
            out.write(base64_encode(request.getMethod().getMethodBytes()));

            out.write("\",\"uri\":\"");
            out.write(base64_encode((request.getRequestURI() + ((request.getQueryString() != null) ? ("?" + request.getQueryString()) : "")).getBytes("ISO-8859-1")));

            out.write("\",\"headers\":[");
            boolean first = true;
            for (String header_name: request.getHeaderNames()) {
                for (String header_value: request.getHeaders(header_name)) {
                    if (first) {
                        first = false;
                    } else {
                        out.write(",");
                    }
                    out.write("[\"");
                    out.write(base64_encode(header_name.getBytes("ISO-8859-1")));
                    out.write("\",\"");
                    out.write(base64_encode(header_value.getBytes("ISO-8859-1")));
                    out.write("\"]");
                }
            }

            out.write("],\"version\":\"");
            out.write(base64_encode(request.getProtocol().getProtocolBytes()));

            out.write("\",\"body\":\"");
            ByteArrayOutputStream body_stream = new ByteArrayOutputStream();
            char[] buf = new char[4096];
            while (true) {
                int read = in.read(buf);
                if (read == -1) {
                    break;
                }
                byte[] the_bytes = new String(buf).substring(0, read).getBytes("ISO-8859-1");
                body_stream.write(the_bytes);
            }

            out.write(base64_encode(body_stream.toByteArray()));
            out.write("\"}");
            out.flush();
        }
    }
}
