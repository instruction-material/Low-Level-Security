use state_model_lab::{Event, Legacy, Session};
use std::process::ExitCode;

const USAGE: &str = "usage: state_model_lab [--from reviewed published reviewer] [review:name | publish | reset ...]";

fn parse(arguments: Vec<String>) -> Result<(Legacy, Vec<Event>), ()> {
    let mut input = Legacy { reviewed: false, published: false, reviewer: None };
    let mut offset = 0;
    if arguments.first().is_some_and(|value| value == "--from") {
        if arguments.len() < 4 {
            return Err(());
        }
        let boolean = |value: &str| match value {
            "0" => Ok(false),
            "1" => Ok(true),
            _ => Err(()),
        };
        input.reviewed = boolean(&arguments[1])?;
        input.published = boolean(&arguments[2])?;
        input.reviewer = (arguments[3] != "-").then(|| arguments[3].clone());
        offset = 4;
    }
    if arguments.is_empty() {
        return Ok((input, vec![Event::Review("Alex".to_owned()), Event::Publish]));
    }
    let events = arguments[offset..].iter().map(|value| {
        if let Some(name) = value.strip_prefix("review:") {
            Ok(Event::Review(name.to_owned()))
        } else {
            match value.as_str() {
                "publish" => Ok(Event::Publish),
                "reset" => Ok(Event::Reset),
                _ => Err(()),
            }
        }
    }).collect::<Result<Vec<_>, _>>()?;
    Ok((input, events))
}

fn main() -> ExitCode {
    let arguments = std::env::args_os().skip(1).map(|value| value.into_string().map_err(|_| ())).collect::<Result<Vec<_>, _>>();
    let Ok((legacy, events)) = arguments.and_then(parse) else {
        eprintln!("{USAGE}");
        return ExitCode::from(64);
    };
    let mut session = match Session::from_legacy(legacy) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error={}", error.code());
            return ExitCode::from(65);
        }
    };
    println!("start={} reviewer={}", session.phase().unwrap().code(), session.reviewer().unwrap_or("-"));
    for (index, event) in events.into_iter().enumerate() {
        if let Err(error) = session.apply(event) {
            eprintln!("error={}", error.code());
            return ExitCode::from(65);
        }
        println!("step={} phase={} reviewer={}", index + 1, session.phase().unwrap().code(), session.reviewer().unwrap_or("-"));
    }
    ExitCode::SUCCESS
}
