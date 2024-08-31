import 'dart:io';
import 'dart:convert';
import 'dart:typed_data';

void main() async {
  final server = await HttpServer.bind(InternetAddress.anyIPv4, 80);
  await server.forEach((HttpRequest request) async {
    String serialized_headers = '';
    bool first = true;
    request.headers.forEach((String name, List<String> values) {
        values.forEach((String value) {
            if (!first) {
                serialized_headers += ',';
            } else {
                first = false;
            }
            serialized_headers += '["${base64.encode(latin1.encode(name))}","${base64.encode(latin1.encode(value))}"]';
        });
    });

    request.response.write('{"method":"${base64.encode(latin1.encode(request.method))}","uri":"${base64.encode(latin1.encode(request.uri.toString()))}","version":"${base64.encode(latin1.encode(request.protocolVersion))}","headers":[${serialized_headers}],"body":"${base64.encode(await (await request.fold<List<int>>([], (List<int> a, Uint8List b) => a + b.toList())).toList())}"}');
    request.response.close();
  });
}
