#![forbid(unsafe_code)]

use std::process::ExitCode;
use typed_record_lab::{first_record, parse_record, public_error};

fn report(value: i32) -> ExitCode {
    if (0..=65535).contains(&value) {
        println!("record=Alpha value={value}");
        return ExitCode::SUCCESS;
    }
    match public_error(value) {
        Some((code, action)) => {
            eprintln!("error={code} action={action}");
            ExitCode::from(65)
        }
        None => {
            eprintln!("error=internal-invariant action=report-error");
            ExitCode::from(70)
        }
    }
}

fn main() -> ExitCode {
    let args: Result<Vec<_>, _> = std::env::args_os()
        .skip(1)
        .map(|arg| arg.into_string())
        .collect();
    let args = match args {
        Ok(args) => args,
        Err(_) => {
            eprintln!("arguments must be valid UTF-8");
            return ExitCode::from(64);
        }
    };
    match args.as_slice() {
        [] => report(parse_record("A:17")),
        [mode, input] if mode == "--record" => report(parse_record(input)),
        [mode, rows @ ..] if mode == "--scan" && rows.len() <= 8 => {
            let rows: Vec<_> = rows.iter().map(String::as_str).collect();
            let (index, value) = first_record(&rows);
            if index == usize::MAX {
                println!("record=absent");
                ExitCode::SUCCESS
            } else {
                report(value)
            }
        }
        _ => {
            eprintln!("usage: typed_record_lab [--record record | --scan [record ...]]");
            ExitCode::from(64)
        }
    }
}
