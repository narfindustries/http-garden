import java.nio.charset.Charset;
import java.util.Base64;
import java.util.Map;
import java.util.Map.Entry;

import io.servicetalk.http.netty.HttpServers;
import io.servicetalk.http.api.HttpSerializers;
import io.servicetalk.http.api.HttpServiceContext;
import io.servicetalk.http.api.HttpResponseFactory;
import io.servicetalk.http.api.HttpResponse;
import io.servicetalk.http.api.HttpProtocolVersion;
import io.servicetalk.http.api.HttpHeaders;
import io.servicetalk.http.api.DefaultHttpHeadersFactory;
import io.servicetalk.http.netty.HttpProtocolConfigs;
import io.servicetalk.http.api.HttpRequestMethod;
import io.servicetalk.buffer.api.Buffer;

public final class GardenServer {
    private static String base64_encode(byte[] input) {
        return Base64.getEncoder().encodeToString(input);
    }

    public static HttpResponse fail(HttpServiceContext ctx, HttpResponseFactory responseFactory) throws Exception {
        ctx.closeAsync().toFuture().get();
        return responseFactory.badRequest();
    }

    public static void main(String[] _unused) throws Exception {
        HttpServers.forPort(80).protocols(HttpProtocolConfigs.h1().headersFactory(new DefaultHttpHeadersFactory(true, true, true)).build()).listenBlockingAndAwait(
            (ctx, req, responseFactory) -> {
                Charset iso_8859_1 = Charset.forName("ISO-8859-1");

                StringBuilder sb = new StringBuilder("{\"headers\":[");
                boolean first = true;
                for (Map.Entry <CharSequence, CharSequence> h: req.headers()) {
                    if (!first) {
                        sb.append(",");
                    }
                    sb.append("[\"")
                      .append(base64_encode(h.getKey().toString().getBytes(iso_8859_1)))
                      .append("\",\"")
                      .append(base64_encode(h.getValue().toString().getBytes(iso_8859_1)))
                      .append("\"]");
                    first = false;
                }
                sb.append("],\"version\":\"");
                sb.append(base64_encode(req.version().toString().getBytes(iso_8859_1
)));
                sb.append("\",\"method\":\"");
                sb.append(base64_encode(req.method().toString().getBytes(iso_8859_1)));
                sb.append("\",\"uri\":\"");
                try {
                    sb.append(base64_encode(req.requestTarget(iso_8859_1).getBytes(iso_8859_1)));
                } catch (java.lang.IllegalArgumentException e) {
                    return fail(ctx, responseFactory);
                }
                sb.append("\",\"body\":\"");
                sb.append(base64_encode(req.payloadBody().toString(iso_8859_1).getBytes(iso_8859_1)));
                sb.append("\"}");

                return responseFactory
                    .ok()
                    .payloadBody(sb.toString(), HttpSerializers.textSerializerAscii());
            }
        ).awaitShutdown();
    }
}
