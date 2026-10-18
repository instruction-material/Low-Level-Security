#![deny(unsafe_op_in_unsafe_fn)]

use boundary_review_lab::checksum;
use std::process::ExitCode;

const USAGE: &str = "usage: boundary_review_lab --help | --case NAME";

fn main() -> ExitCode {
    let args: Vec<_> = std::env::args_os().skip(1).take(3).collect();
    if args.len() == 1 && args[0] == "--help" {
        println!("{USAGE}");
        return ExitCode::SUCCESS;
    }
    let case = if args.len() == 2 && args[0] == "--case" { args[1].to_str() } else { None };
    let bytes: &[u8] = match case {
        Some("empty") => &[],
        Some("valid") => &[7, 17],
        Some("cap") => &[255; 8],
        Some("over") => &[0; 9],
        _ => {
            eprintln!("{USAGE}");
            return ExitCode::from(64);
        }
    };
    match checksum(bytes) {
        Ok(sum) => {
            println!("length={} checksum={sum}", bytes.len());
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("error={}", error.code());
            ExitCode::from(65)
        }
    }
}
