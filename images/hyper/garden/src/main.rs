use std::{convert::Infallible, error::Error};

use base64::{Engine as _, engine::general_purpose};
use bytes::Bytes;
use http_body_util::{BodyExt, Full, combinators::BoxBody};
use hyper::{Request, Version, body, http::Response, service::service_fn};
use hyper_util::{
    rt::{TokioExecutor, TokioIo},
    server::conn::auto::Builder,
};
use tokio::{net::TcpListener, task::JoinSet};

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Box<dyn Error + Send + Sync + 'static>> {
    let tcp_listener = TcpListener::bind("0.0.0.0:80").await?;

    let mut join_set = JoinSet::new();
    loop {
        let (stream, _) = match tcp_listener.accept().await {
            Ok(x) => x,
            Err(_) => {
                eprintln!("Accept failed!");
                continue;
            }
        };

        join_set.spawn(async move {
            let _ = Builder::new(TokioExecutor::new())
                .serve_connection(
                    TokioIo::new(stream),
                    service_fn(async |req: Request<body::Incoming>| {
                        let mut result = "{\"method\":\"".to_owned()
                            + &general_purpose::STANDARD.encode(req.method().to_string())
                            + "\",\"version\":\""
                            + &general_purpose::STANDARD.encode(match req.version() {
                                Version::HTTP_09 => "0.9",
                                Version::HTTP_10 => "1.0",
                                Version::HTTP_11 => "1.1",
                                Version::HTTP_2 => "2",
                                Version::HTTP_3 => "3",
                                _ => panic!("Unexpected HTTP version!"),
                            })
                            + "\",\"uri\":\""
                            + &general_purpose::STANDARD.encode(req.uri().to_string())
                            + "\",\"headers\":[";
                        let mut first = true;
                        for (k, v) in req.headers() {
                            if first {
                                first = false;
                            } else {
                                result += ",";
                            }
                            result += &("[\"".to_owned()
                                + &general_purpose::STANDARD.encode(k.to_string())
                                + "\",\""
                                + &general_purpose::STANDARD.encode(v.as_bytes())
                                + "\"]");
                        }

                        result += &("],\"body\":\"".to_owned()
                            + &(general_purpose::STANDARD.encode(req.collect().await?.to_bytes())
                                + "\"}"));
                        Ok::<Response<BoxBody<bytes::Bytes, Infallible>>, hyper::Error>(
                            Response::builder()
                                .body(Full::new(Bytes::from(result)).boxed())
                                .expect("This cannot happen"),
                        )
                    }),
                )
                .await;
        });
    }
}
