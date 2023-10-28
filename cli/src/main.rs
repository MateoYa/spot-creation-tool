// use clap::{Parser, Subcommand};
// mod commands;
// //#[clap(author="MateoE Yajure", version, about="Api Call")]
// #[derive(Parser)]
// struct Arguments {
//     #[clap(subcommand)]
//     cmd: SubCommand,
// }
// #[derive(Subcommand, Debug)]
// enum SubCommand {
//     Setup{
//         //#[clap(forbid_empty_values = true, validator = validate_package_name)]
//         #[clap(default_value_t=0,short, long)]
//         max_depth: usize,
//         package_name: String,

//     },
//     // Create{
//     //     platform: String,
//     //     #[clap(default_value_t=usize::MAX,short, long)]
//     //     amount: usize,
//     // }
// }

// fn CreateApi(platform: &str, amount: usize) -> std::io::Result<usize>{
//     println!("{}", platform);
//     println!("{}", amount);

//     return Ok(2);
// }

// fn main() {
//     let args = Arguments::parse();
//     match args.cmd {
//         SubCommand::Setup { package_name, max_depth } => match commands::CreateApi(&package_name, max_depth){ 
//             Ok(c) => println!("{} uses found", c),
//             Err(e) => println!("error in processing : {}", e),
//         },
//         // SubCommand::Create {
//         //     platform,
//         //     amount,
//         // } => {/* TODO */}
//     }
// }



// // mod commands;
// // use clap::Parser;

// // /// Doc comment
// // #[derive(Parser)]
// // //[clap(author, version, about, long_about = None)]
// // enum Cli {
// //     /// Doc comment
// //     // #[clap(subcommand)]
// //     // apikey: commands::key::Command,
    
// // }

// // fn main() {
// //     let cli = Cli::parse();
// //     cli.apikey.run();
// // }

use reqwest::{Client, Error};

async fn post_it() -> Result<(), Error> {
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

#[tokio::main]
async fn main() -> Result<(), Error> {
    post_it().await?;
    Ok(())
}
