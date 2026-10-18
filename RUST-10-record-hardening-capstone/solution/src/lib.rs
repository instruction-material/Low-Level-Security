#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    One,
    Two,
    Three,
}

impl Kind {
    pub fn value(self) -> u8 {
        match self {
            Self::One => 1,
            Self::Two => 2,
            Self::Three => 3,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Record {
    label: String,
    kind: Kind,
}

impl Record {
    pub fn label(&self) -> &str {
        &self.label
    }

    pub fn kind(&self) -> Kind {
        self.kind
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ParseError {
    TooLarge,
    Empty,
    EmptyLabel,
    LabelTooLong,
    TruncatedLabel,
    MissingKind,
    TrailingData,
    InvalidUtf8,
    UnsupportedKind,
}

impl ParseError {
    pub fn code(self) -> &'static str {
        match self {
            Self::TooLarge => "too-large",
            Self::Empty => "empty",
            Self::EmptyLabel => "empty-label",
            Self::LabelTooLong => "label-too-long",
            Self::TruncatedLabel => "truncated-label",
            Self::MissingKind => "missing-kind",
            Self::TrailingData => "trailing-data",
            Self::InvalidUtf8 => "invalid-utf8",
            Self::UnsupportedKind => "unsupported-kind",
        }
    }
}

pub fn parse_record(input: &[u8]) -> Result<Record, ParseError> {
    if input.len() > 12 {
        return Err(ParseError::TooLarge);
    }
    let (&declared, tail) = input.split_first().ok_or(ParseError::Empty)?;
    if declared == 0 {
        return Err(ParseError::EmptyLabel);
    }
    if declared > 10 {
        return Err(ParseError::LabelTooLong);
    }
    let (label, rest) = tail
        .split_at_checked(usize::from(declared))
        .ok_or(ParseError::TruncatedLabel)?;
    let (&kind, trailing) = rest.split_first().ok_or(ParseError::MissingKind)?;
    if !trailing.is_empty() {
        return Err(ParseError::TrailingData);
    }
    let label = std::str::from_utf8(label).map_err(|_| ParseError::InvalidUtf8)?;
    let kind = match kind {
        1 => Kind::One,
        2 => Kind::Two,
        3 => Kind::Three,
        _ => return Err(ParseError::UnsupportedKind),
    };
    Ok(Record {
        label: label.to_owned(),
        kind,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cat_contract() {
        let record = parse_record(&[3, 99, 97, 116, 1]).unwrap();
        assert_eq!(record.label(), "cat");
        assert_eq!(record.kind(), Kind::One);
    }

    #[test]
    fn every_supported_kind() {
        for value in 1..=3 {
            let record = parse_record(&[1, b'x', value]).unwrap();
            assert_eq!(record.kind().value(), value);
        }
    }

    #[test]
    fn unicode_uses_byte_length() {
        let record = parse_record(&[3, 0xe2, 0x98, 0x83, 2]).unwrap();
        assert_eq!(record.label(), "☃");
        assert_eq!(record.label().len(), 3);
        assert_eq!(record.label().chars().count(), 1);
    }

    #[test]
    fn exact_maximum_is_valid() {
        let mut input = vec![10];
        input.extend_from_slice(b"abcdefghij");
        input.push(3);
        assert_eq!(parse_record(&input).unwrap().label(), "abcdefghij");
    }

    #[test]
    fn result_owns_label() {
        let mut input = vec![3, 99, 97, 116, 1];
        let record = parse_record(&input).unwrap();
        input.fill(0);
        drop(input);
        assert_eq!(record.label(), "cat");
    }

    #[test]
    fn overall_bound_precedes_structure() {
        assert_eq!(parse_record(&[0; 13]), Err(ParseError::TooLarge));
    }

    #[test]
    fn empty_input() {
        assert_eq!(parse_record(&[]), Err(ParseError::Empty));
    }

    #[test]
    fn length_rules_precede_slicing() {
        assert_eq!(parse_record(&[0, 1]), Err(ParseError::EmptyLabel));
        assert_eq!(parse_record(&[255]), Err(ParseError::LabelTooLong));
    }

    #[test]
    fn short_label() {
        assert_eq!(parse_record(&[3, 99, 97]), Err(ParseError::TruncatedLabel));
    }

    #[test]
    fn kind_must_be_present() {
        assert_eq!(parse_record(&[1, 97]), Err(ParseError::MissingKind));
    }

    #[test]
    fn trailing_before_encoding_and_kind() {
        assert_eq!(parse_record(&[1, 255, 9, 0]), Err(ParseError::TrailingData));
    }

    #[test]
    fn encoding_before_kind() {
        assert_eq!(parse_record(&[1, 255, 9]), Err(ParseError::InvalidUtf8));
    }

    #[test]
    fn unsupported_kind() {
        assert_eq!(parse_record(&[1, 97, 9]), Err(ParseError::UnsupportedKind));
    }
}
