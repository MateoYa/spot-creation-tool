use std::collections::VecDeque;
use std::fs;
use std::path::PathBuf;
use clap::{Parser, Subcommand};
mod commands;
//#[clap(author="MateoE Yajure", version, about="Api Call")]
#[derive(Parser)]
struct Arguments {
    #[clap(subcommand)]
    cmd: SubCommand,
}
#[derive(Subcommand, Debug)]
enum SubCommand {
    Setup{
        //#[clap(forbid_empty_values = true, validator = validate_package_name)]
        #[clap(default_value_t=0,short, long)]
        max_depth: usize,
        package_name: String,

    },
    // Create{
    //     platform: String,
    //     #[clap(default_value_t=usize::MAX,short, long)]
    //     amount: usize,
    // }
}

fn CreateApi(platform: &str, amount: usize) -> std::io::Result<usize>{
    println!("{}", platform);
    println!("{}", amount);

    return Ok(2);
}

fn main() {
    let args = Arguments::parse();
    match args.cmd {
        SubCommand::Setup { package_name, max_depth } => match commands::CreateApi(&package_name, max_depth){ 
            Ok(c) => println!("{} uses found", c),
            Err(e) => println!("error in processing : {}", e),
        },
        // SubCommand::Create {
        //     platform,
        //     amount,
        // } => {/* TODO */}
    }
}



// mod commands;
// use clap::Parser;

// /// Doc comment
// #[derive(Parser)]
// //[clap(author, version, about, long_about = None)]
// enum Cli {
//     /// Doc comment
//     // #[clap(subcommand)]
//     // apikey: commands::key::Command,
    
// }

// fn main() {
//     let cli = Cli::parse();
//     cli.apikey.run();
// }
