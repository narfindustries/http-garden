import 'dart:async';
import 'dart:io';
import 'dart:convert';
import 'dart:typed_data';

Future<void> main() async {
  while (true) {
    await runZoned(() async {
      final server = await HttpServer.bind(InternetAddress.anyIPv4, 80);
      await server.forEach((HttpRequest request) async {
        String serialized_headers = '';
        bool first = true;
        request.headers.forEach((String name, List<String> values) async {
          values.forEach((String value) {
            if (!first) {
              serialized_headers += ',';
            } else {
              first = false;
            }
            serialized_headers +=
                '["${base64.encode(latin1.encode(name))}","${base64.encode(latin1.encode(value))}"]';
          });
        });
        String body = base64.encode(await (await request.fold<List<int>>(
                [], (List<int> a, Uint8List b) => a + b.toList()))
            .toList());
        String method = base64.encode(latin1.encode(request.method));
        String uri = base64.encode(latin1.encode(request.uri.toString()));
        String version = base64.encode(latin1.encode(request.protocolVersion));
        request.response.write(
            '{"method":"${method}","uri":"${uri}","version":"${version}","headers":[${serialized_headers}],"body":"${body}"}');
        request.response.close();
      });
    },
        zoneSpecification: ZoneSpecification(
            handleUncaughtError: (_self, _parent, _zone, error, _stackTrace) =>
                print(error.toString())));
  }
}
