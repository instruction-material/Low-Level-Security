#![forbid(unsafe_code)]

use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RecordKind {
    Alpha,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Record {
    pub kind: RecordKind,
    pub value: u16,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ParseError {
    MissingSeparator,
    UnknownKind,
    MissingValue,
    InvalidNumber,
    ValueOutOfRange,
}

impl ParseError {
    pub fn code(self) -> &'static str {
        match self {
            Self::MissingSeparator => "missing-separator",
            Self::UnknownKind => "unknown-kind",
            Self::MissingValue => "missing-value",
            Self::InvalidNumber => "invalid-number",
            Self::ValueOutOfRange => "value-out-of-range",
        }
    }

    pub fn action(self) -> &'static str {
        match self {
            Self::MissingSeparator => "add-separator",
            Self::UnknownKind => "choose-A",
            Self::MissingValue => "supply-value",
            Self::InvalidNumber => "use-ASCII-digits",
            Self::ValueOutOfRange => "use-u16-range",
        }
    }
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.code())
    }
}

impl std::error::Error for ParseError {}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RowError {
    pub index: usize,
    pub error: ParseError,
}

impl fmt::Display for RowError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "record rejected: {}", self.error)
    }
}

impl std::error::Error for RowError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        Some(&self.error)
    }
}

fn parse_value(value: &str) -> Result<u16, ParseError> {
    if value.is_empty() {
        return Err(ParseError::MissingValue);
    }
    if !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ParseError::InvalidNumber);
    }
    value.parse().map_err(|_| ParseError::ValueOutOfRange)
}

pub fn parse_record(input: &str) -> Result<Record, ParseError> {
    let (kind, value) = input.split_once(':').ok_or(ParseError::MissingSeparator)?;
    if kind != "A" {
        return Err(ParseError::UnknownKind);
    }
    let value = parse_value(value)?;
    Ok(Record {
        kind: RecordKind::Alpha,
        value,
    })
}

pub fn first_record(rows: &[&str]) -> Result<Option<Record>, RowError> {
    let Some((index, row)) = rows.iter().enumerate().find(|(_, row)| !row.is_empty()) else {
        return Ok(None);
    };
    let record = parse_record(row).map_err(|error| RowError { index, error })?;
    Ok(Some(record))
}

pub fn all_records(rows: &[&str]) -> Vec<Result<Record, RowError>> {
    rows.iter()
        .enumerate()
        .filter(|(_, row)| !row.is_empty())
        .map(|(index, row)| parse_record(row).map_err(|error| RowError { index, error }))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn alpha(value: u16) -> Record {
        Record {
            kind: RecordKind::Alpha,
            value,
        }
    }

    fn context(index: usize, error: ParseError) -> RowError {
        RowError { index, error }
    }

    #[test]
    fn preserves_every_u16_value() {
        for value in 0..=u16::MAX {
            assert_eq!(parse_record(&format!("A:{value}")), Ok(alpha(value)));
        }
    }

    #[test]
    fn keeps_five_error_classes_distinct() {
        let cases = [
            ("A17", ParseError::MissingSeparator),
            ("B:17", ParseError::UnknownKind),
            ("A:", ParseError::MissingValue),
            ("A:x", ParseError::InvalidNumber),
            ("A:65536", ParseError::ValueOutOfRange),
        ];
        for (input, error) in cases {
            assert_eq!(parse_record(input), Err(error));
        }
    }

    #[test]
    fn accepts_leading_zeros_without_a_false_width_limit() {
        assert_eq!(parse_record("A:00017"), Ok(alpha(17)));
        assert_eq!(parse_record("A:0000065535"), Ok(alpha(65535)));
        let input = format!("A:{}65535", "0".repeat(96));
        assert_eq!(parse_record(&input), Ok(alpha(65535)));
    }

    #[test]
    fn rejects_extra_separators_whitespace_unicode_and_nul() {
        for input in ["A:17:2", "A:17 ", "A: 17", "A:+17", "A:١٧", "A:1\0"] {
            assert_eq!(parse_record(input), Err(ParseError::InvalidNumber));
        }
    }

    #[test]
    fn absence_is_not_the_valid_zero_record() {
        assert_eq!(first_record(&[]), Ok(None));
        assert_eq!(first_record(&["", ""]), Ok(None));
        assert_eq!(first_record(&["", "A:0"]), Ok(Some(alpha(0))));
    }

    #[test]
    fn first_candidate_retains_context_and_does_not_skip_errors() {
        let result = first_record(&["", "A:", "A:17"]);
        assert_eq!(result, Err(context(1, ParseError::MissingValue)));
        assert_eq!(first_record(&["A:17", "B:0"]), Ok(Some(alpha(17))));
    }

    #[test]
    fn collection_keeps_successes_and_indexed_errors() {
        let expected = vec![
            Ok(alpha(17)),
            Err(context(2, ParseError::UnknownKind)),
            Ok(alpha(0)),
        ];
        assert_eq!(all_records(&["", "A:17", "B:0", "A:0"]), expected);
    }

    #[test]
    fn public_actions_are_distinct_and_do_not_echo_input() {
        let mut actions = Vec::new();
        let errors = [
            ParseError::MissingSeparator,
            ParseError::UnknownKind,
            ParseError::MissingValue,
            ParseError::InvalidNumber,
            ParseError::ValueOutOfRange,
        ];
        for error in errors {
            assert!(!error.to_string().contains("PRIVATE_MARKER"));
            actions.push(error.action());
        }
        actions.sort_unstable();
        actions.dedup();
        assert_eq!(actions.len(), 5);
        let error = context(2, ParseError::InvalidNumber);
        assert_eq!(error.to_string(), "record rejected: invalid-number");
        assert!(std::error::Error::source(&error).is_some());
    }
}
