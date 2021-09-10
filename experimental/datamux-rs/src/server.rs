use tonic::{transport::Server, Request, Response, Status};

use datamux::greeter_server::{Greeter, GreeterServer};
use datamux::{HelloReply, HelloRequest};

pub mod datamux {
    tonic::include_proto!("datamux");
}

#[derive(Debug, Default)]
pub struct MyGreeter {}

#[tonic::async_trait]
impl Greeter for MyGreeter {
    async fn say_hello(&self, request: Request<HelloRequest>) -> Result<Response<HelloReply>, Status> {
        println!("Got a request: {:?}", request);
        let reply = datamux::HelloReply {
            message: format!("Hello {}!", request.into_inner().name).into()
        };
        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let greeter = MyGreeter::default();
    Server::builder()
        .add_service(GreeterServer::new(greeter))
        .serve(addr)
        .await?;
    Ok(())
}
