use label_slice_lab::{WindowError, byte_window, char_window, sanitize, str_window};
use std::process::ExitCode;

fn fail(message: &str, status: u8) -> ExitCode {
    eprintln!("{message}");
    ExitCode::from(status)
}

fn index(text: &str) -> Option<usize> {
    if text.is_empty() || !text.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

fn rejected(error: WindowError) -> ExitCode {
    fail(&format!("error={}", error.code()), 65)
}

fn main() -> ExitCode {
    let args: Result<Vec<String>, _> = std::env::args_os()
        .skip(1)
        .map(|arg| arg.into_string())
        .collect();
    let Ok(args) = args else {
        return fail("arguments must be valid UTF-8", 64);
    };
    if args.is_empty() {
        println!("label={}", sanitize("packet-42!"));
        return ExitCode::SUCCESS;
    }
    if args.len() == 2 && args[0] == "--sanitize" {
        println!("label={}", sanitize(&args[1]));
        return ExitCode::SUCCESS;
    }
    if args.len() != 4 || !matches!(args[0].as_str(), "--window" | "--bytes" | "--chars") {
        return fail("usage: label_slice_lab [--sanitize text | --window text start end | --bytes text start end | --chars text start end]", 64);
    }
    let (Some(start), Some(end)) = (index(&args[2]), index(&args[3])) else {
        return fail("indices must be ASCII decimal usize values", 64);
    };
    if args[0] == "--bytes" {
        return match byte_window(args[1].as_bytes(), start, end) {
            Ok(bytes) => {
                println!("bytes={bytes:?}");
                ExitCode::SUCCESS
            }
            Err(error) => rejected(error),
        };
    }
    let selected = if args[0] == "--chars" {
        char_window(&args[1], start, end)
    } else {
        str_window(&args[1], start, end)
    };
    match selected {
        Ok(text) => {
            println!(
                "window={} bytes={} scalars={}",
                text,
                text.len(),
                text.chars().count()
            );
            ExitCode::SUCCESS
        }
        Err(error) => rejected(error),
    }
}
