use clap::{Parser, Subcommand};
use reqwest;

pub fn CreateApi(platform: &str, amount: usize) -> std::io::Result<usize>{
    println!("{}", platform);
    println!("hey {}", amount);
    let params = [("foo", "bar"), ("baz", "quux")];
    let client = reqwest::Client::new();
    let res = client.post("http://127.0.0.1:5000/aws/create")
        .form(&params)
        .send();
    return Ok(amount);
}

use reqwest::{Client, Error};

async fn CreateApi() -> Result<(), Error> {
    let url = "http://127.0.0.1:5000/aws/create";
    let json_data = r#"{"name": "John Doe", "email": "john.doe@example.com"}"#;

    let client = reqwest::Client::new();

    let response = client
        .post(url)
        .header("Content-Type", "application/json")
        .body(json_data.to_owned())
        .send()
        .await?;

    println!("Status: {}", response.status());

    let response_body = response.text().await?;
    println!("Response body:\n{}", response_body);

    Ok(())
}
