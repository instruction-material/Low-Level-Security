#![forbid(unsafe_code)]

use concurrency_lab::{Job, Mode, run};
use std::process::ExitCode;

const USAGE: &str = "usage: concurrency_lab --help | --case NAME";

fn main() -> ExitCode {
    let args: Vec<_> = std::env::args_os().skip(1).take(3).collect();
    if args.len() == 1 && args[0] == "--help" {
        println!("{USAGE}");
        return ExitCode::SUCCESS;
    }
    let case = if args.len() == 2 && args[0] == "--case" {
        args[1].to_str()
    } else {
        None
    };
    let valid = || vec![Job { id: 3, value: 17 }, Job { id: 0, value: 7 }];
    let (jobs, mode) = match case {
        Some("empty") => (Vec::new(), Mode::Normal),
        Some("valid") => (valid(), Mode::Normal),
        Some("cap") => ((0..8).map(|id| Job { id, value: u16::MAX }).collect(), Mode::Normal),
        Some("fail") => (valid(), Mode::FailItem(3)),
        Some("cancel") => (valid(), Mode::CancelBeforeStart),
        Some("duplicate") => (vec![Job { id: 0, value: 1 }; 2], Mode::Normal),
        Some("invalid-id") => (vec![Job { id: 8, value: 1 }], Mode::Normal),
        Some("over") => (vec![Job { id: 0, value: 1 }; 9], Mode::Normal),
        _ => {
            eprintln!("{USAGE}");
            return ExitCode::from(64);
        }
    };
    match run(jobs, mode).report {
        Ok(report) => {
            print!("{}", report.render());
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("error={}", error.code());
            ExitCode::from(65)
        }
    }
}
