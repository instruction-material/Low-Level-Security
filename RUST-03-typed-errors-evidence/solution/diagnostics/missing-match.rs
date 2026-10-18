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
    }
}

fn main() {
    println!("{}", code(ParseError::ValueOutOfRange));
}
