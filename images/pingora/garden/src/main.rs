use async_trait::async_trait;
use base64::{Engine as _, engine::general_purpose};
use bytes::Bytes;
use http::{Response, StatusCode, Version};

use pingora::apps::http_app::{HttpServer, ServeHttp};
use pingora::protocols::http::ServerSession;
use pingora::server::Server;
use pingora::server::configuration::Opt;
use pingora::services::listening::Service;

struct GardenServer;

#[async_trait]
impl ServeHttp for GardenServer {
    async fn response(&self, http_stream: &mut ServerSession) -> Response<Vec<u8>> {
        let mut chunks = Vec::new();
        while let Some(chunk) = http_stream.read_request_body().await.unwrap() {
            chunks.push(chunk);
        };

        let _ = http_stream.read_request().await.unwrap();
        let header = http_stream.req_header();
        let parts = header.as_owned_parts();

        let result_bytes = Bytes::from(
            "{\"body\":\"".to_owned()
                + &general_purpose::STANDARD.encode(chunks.concat())
                + "\",\"uri\":\""
                + &general_purpose::STANDARD.encode(header.raw_path())
                + "\",\"version\":\""
                + &general_purpose::STANDARD.encode(match parts.version {
                    Version::HTTP_09 => "0.9",
                    Version::HTTP_10 => "1.0",
                    Version::HTTP_11 => "1.1",
                    Version::HTTP_2 => "2",
                    Version::HTTP_3 => "3",
                    _ => panic!("Impossible HTTP version encountered!"),
                })
                + "\",\"method\":\""
                + &general_purpose::STANDARD.encode(parts.method.as_str())
                + "\",\"headers\":["
                + &parts
                    .headers
                    .into_iter()
                    .map(|(k, v)| {
                        "[\"".to_owned()
                            + &general_purpose::STANDARD.encode(k.unwrap().to_string())
                            + "\",\""
                            + &general_purpose::STANDARD.encode(v.as_bytes())
                            + "\"]"
                    })
                    .collect::<Vec<_>>()
                    .join(",")
                + "]}",
        );
        Response::builder()
            .status(StatusCode::OK)
            .header(http::header::CONTENT_LENGTH, result_bytes.len())
            .body(result_bytes.to_vec())
            .unwrap()
    }
}

fn main() {
    let mut the_service = Service::new("Garden".to_string(), HttpServer::new_app(GardenServer));
    the_service.add_tcp("0.0.0.0:80");

    let mut the_server = Server::new(Opt {
        upgrade: false,
        daemon: false,
        nocapture: false,
        test: false,
        conf: None,
    })
    .unwrap();
    the_server.bootstrap();
    the_server.add_service(the_service);
    the_server.run_forever();
}
