use std::net::SocketAddr;

use base64::{Engine as _, engine::general_purpose};
use bytes::Bytes;
use http_body_util::{combinators::BoxBody, BodyExt, Full};
use hyper::server::conn::http2;
use hyper::service::service_fn;
use hyper::{Version, Request, Response};
use tokio::net::TcpListener;

#[path = "../benches/support/mod.rs"]
mod support;
use support::TokioIo;

#[derive(Clone)]
pub struct TokioExecutor;

impl<F> hyper::rt::Executor<F> for TokioExecutor
where
    F: std::future::Future + Send + 'static,
    F::Output: Send + 'static,
{
    fn execute(&self, fut: F) {
        tokio::task::spawn(fut);
    }
}

async fn echo(
    req: Request<hyper::body::Incoming>,
) -> Result<Response<BoxBody<Bytes, hyper::Error>>, hyper::Error> {
    let method = general_purpose::STANDARD.encode(req.method().to_string());
    let version = general_purpose::STANDARD.encode(
        match req.version() {
            Version::HTTP_09 => "0.9",
            Version::HTTP_10 => "1.0",
            Version::HTTP_11 => "1.1",
            Version::HTTP_2 => "2",
            Version::HTTP_3 => "3",
            _ => "",
        }
    );
    let uri = general_purpose::STANDARD.encode(req.uri().to_string());
    let mut result = "{\"method\":\"".to_owned() + &method + "\",\"version\":\"" + &version + "\",\"uri\":\"" + &uri + "\",\"headers\":[";
    let mut first = true;
    for (k, v) in req.headers() {
        if !first {
            result += ",";
        }
        first = false;
        result += &("[\"".to_owned()
                + &general_purpose::STANDARD.encode(k.to_string())
                + "\",\""
                + &general_purpose::STANDARD.encode(v.as_bytes())
                + "\"]");
    }

    result += "],\"body\":\"";
    let body = general_purpose::STANDARD.encode(req.collect().await?.to_bytes());
    result += &(body + "\"}");
    Ok(Response::new(full(result)))
}

fn full<T: Into<Bytes>>(chunk: T) -> BoxBody<Bytes, hyper::Error> {
    Full::new(chunk.into())
        .map_err(|never| match never {})
        .boxed()
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let addr = SocketAddr::from(([0, 0, 0, 0], 80));

    let listener = TcpListener::bind(addr).await?;
    println!("Listening on http://{}", addr);
    loop {
        let (stream, _) = listener.accept().await?;
        let io = TokioIo::new(stream);

        tokio::task::spawn(async move {
            if let Err(err) = http2::Builder::new(TokioExecutor)
                .serve_connection(io, service_fn(echo))
                .await
            {
                println!("Error serving connection: {:?}", err);
            }
        });
    }
}