#![forbid(unsafe_code)]

use std::env;
use std::process::ExitCode;
use trait_pipeline_lab::{MemoryRows, all_records, audit};

fn usage() -> ExitCode {
    eprintln!("usage: trait_pipeline_lab [--audit | --all] [row ...; at most 16]");
    ExitCode::from(64)
}

fn main() -> ExitCode {
    let Ok(mut arguments) = env::args_os().skip(1).map(|arg| arg.into_string()).collect::<Result<Vec<_>, _>>() else {
        return usage();
    };
    let (all, rows) = if arguments.is_empty() {
        (false, vec!["alpha=7".to_owned(), "beta=17".to_owned()])
    } else {
        let mode = arguments.remove(0);
        if (mode != "--audit" && mode != "--all") || arguments.len() > 16 {
            return usage();
        }
        (mode == "--all", arguments)
    };
    let source = MemoryRows::new(rows);
    let mut failed = false;
    if all {
        for (index, outcome) in all_records(&source).iter().enumerate() {
            match outcome {
                Ok(record) => println!("row={} label={} value={}", index + 1, record.label, record.value),
                Err(error) => {
                    println!("row={} error={}", error.index, error.kind.code());
                    failed = true;
                }
            }
        }
    } else {
        match audit(&source) {
            Ok(report) => println!("count={} total={} labels={}", report.labels.len(), report.total, if report.labels.is_empty() { "-".to_owned() } else { report.labels.join("|") }),
            Err(error) => {
                eprintln!("row={} error={}", error.index, error.kind.code());
                failed = true;
            }
        }
    }
    println!("pulls={}", source.pulls());
    ExitCode::from(if failed { 65 } else { 0 })
}
