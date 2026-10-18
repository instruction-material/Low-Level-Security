mod fixtures;

use record_hardening_lab::parse_record;
use std::process::ExitCode;

const USAGE: &str = "usage: record_hardening_lab --help | --case NAME";

fn main() -> ExitCode {
    let arguments: Vec<_> = std::env::args_os().skip(1).take(3).collect();
    if arguments.len() == 1 && arguments[0] == "--help" {
        println!("{USAGE}");
        return ExitCode::SUCCESS;
    }
    if arguments.len() != 2 || arguments[0] != "--case" {
        eprintln!("{USAGE}");
        return ExitCode::from(64);
    }
    let Some(input) = arguments[1].to_str().and_then(fixtures::select) else {
        eprintln!("{USAGE}");
        return ExitCode::from(64);
    };
    match parse_record(input) {
        Ok(record) => {
            println!(
                "kind={} label-bytes={}",
                record.kind().value(),
                record.label().len()
            );
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("error={}", error.code());
            ExitCode::from(65)
        }
    }
}
