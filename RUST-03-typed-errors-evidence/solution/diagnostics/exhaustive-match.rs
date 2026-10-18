#[derive(Clone, Copy)]
enum ParseError {
    MissingSeparator,
    UnknownKind,
    MissingValue,
    InvalidNumber,
    ValueOutOfRange,
}
fn code(error: ParseError) -> &'static str {
    match error {
        ParseError::MissingSeparator => "missing-separator",
        ParseError::UnknownKind => "unknown-kind",
        ParseError::MissingValue => "missing-value",
        ParseError::InvalidNumber => "invalid-number",
        ParseError::ValueOutOfRange => "value-out-of-range",
    }
}

fn main() {
    for error in [
        ParseError::MissingSeparator,
        ParseError::UnknownKind,
        ParseError::MissingValue,
        ParseError::InvalidNumber,
        ParseError::ValueOutOfRange,
    ] {
        println!("{}", code(error));
    }
}
