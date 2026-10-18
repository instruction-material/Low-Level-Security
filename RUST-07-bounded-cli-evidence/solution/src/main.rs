use bounded_cli_lab::{Arguments, Error, USAGE, load_fixture, parse_arguments, process};
use std::process::ExitCode;

fn execute() -> Result<(), Error> {
    let arguments = std::env::args_os().skip(1).take(3).collect::<Vec<_>>();
    match parse_arguments(&arguments)? {
        Arguments::Help => print!("{USAGE}"),
        Arguments::File(name) => {
            let bytes = load_fixture(&name)?;
            let report = process(&bytes)?;
            print!("{report}");
        }
    }
    Ok(())
}

fn main() -> ExitCode {
    match execute() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => { eprint!("{}", error.diagnostic()); ExitCode::from(error.status()) }
    }
}
