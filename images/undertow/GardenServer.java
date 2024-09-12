import java.io.IOException;
import io.undertow.io.Receiver;
import io.undertow.util.HttpString;
import java.io.ByteArrayOutputStream;
import java.util.Base64;
import io.undertow.io.Sender;
import io.undertow.Undertow;
import io.undertow.server.HttpHandler;
import io.undertow.server.HttpServerExchange;
import io.undertow.server.BlockingHttpExchange;
import io.undertow.util.Headers;
import io.undertow.util.HeaderValues;

public class GardenServer {
    private static String base64_encode(byte[] input) {
        return Base64.getEncoder().encodeToString(input);
    }

    private static byte[] httpstring_to_bytes(HttpString hs) throws IOException {
        final ByteArrayOutputStream s = new ByteArrayOutputStream();
        hs.writeTo(s);
        return s.toByteArray();
    }

    public static void main(final String[] args) {
        Undertow server = Undertow.builder()
                .addHttpListener(80, "0.0.0.0")
                .setHandler(new HttpHandler() {
                    @Override
                    public void handleRequest(final HttpServerExchange exchange) throws IOException {
                        final Sender sender = exchange.getResponseSender();
                        final Receiver receiver = exchange.getRequestReceiver();

                        final String query = exchange.getQueryString();
                        final String uri = exchange.getRequestURI() + (query != "" ? "?" + query : "");
                        
                        String headers = "";
                        boolean first = true;
                        for (HeaderValues hv : exchange.getRequestHeaders()) {
                            for (String v : hv) {
                                if (first) {
                                    first = false;
                                } else {
                                    headers += ",";
                                }
                                headers += "[\"" + base64_encode(httpstring_to_bytes(hv.getHeaderName())) + "\",\"" + base64_encode(v.getBytes("ISO-8859-1")) + "\"]";
                            }
                        }
                        
                        final ByteArrayOutputStream body_stream = new ByteArrayOutputStream();
                        receiver.receiveFullBytes((ex, body) -> {
                            body_stream.write(body, 0, body.length);
                        });

                        sender.send(
                            "{\"uri\":\""
                            + base64_encode(uri.getBytes("ISO-8859-1"))
                            + "\",\"method\":\""
                            + base64_encode(httpstring_to_bytes(exchange.getRequestMethod()))
                            + "\",\"version\":\""
                            + base64_encode(httpstring_to_bytes(exchange.getProtocol()))
                            + "\",\"headers\":["
                            + headers
                            + "],\"body\":\""
                            + base64_encode(body_stream.toByteArray())
                            + "\"}"
                        );
                    }
                }).build();
        server.start();
    }
}
