use clap::{Parser, Subcommand};


pub fn CreateApi(platform: &str, amount: usize) -> std::io::Result<usize>{
    println!("{}", platform);
    println!("{}", amount);

    return Ok(amount);
}