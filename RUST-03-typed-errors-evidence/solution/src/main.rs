#![forbid(unsafe_code)]

use std::process::ExitCode;
use typed_record_lab::{ParseError, Record, first_record, parse_record};

fn report(result: Result<Option<Record>, ParseError>) -> ExitCode {
    match result {
        Ok(Some(record)) => {
            println!("record={:?} value={}", record.kind, record.value);
            ExitCode::SUCCESS
        }
        Ok(None) => {
            println!("record=absent");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("error={} action={}", error.code(), error.action());
            ExitCode::from(65)
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
        [] => report(parse_record("A:17").map(Some)),
        [mode, input] if mode == "--record" => report(parse_record(input).map(Some)),
        [mode, rows @ ..] if mode == "--scan" && rows.len() <= 8 => {
            let rows: Vec<_> = rows.iter().map(String::as_str).collect();
            report(first_record(&rows).map_err(|error| error.error))
        }
        _ => {
            eprintln!("usage: typed_record_lab [--record record | --scan [record ...]]");
            ExitCode::from(64)
        }
    }
}
