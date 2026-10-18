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
    Unclassified,
}

impl ParseError {
    pub fn code(self) -> &'static str {
        match self {
            Self::TooLarge => "too-large",
            Self::Unclassified => "unclassified",
        }
    }
}

// This safe baseline preserves valid behavior. Split its combined refusals
// into the documented typed errors and explain their precedence.
pub fn parse_record(input: &[u8]) -> Result<Record, ParseError> {
    if input.len() > 12 {
        return Err(ParseError::TooLarge);
    }
    let Some((&declared, tail)) = input.split_first() else {
        return Err(ParseError::Unclassified);
    };
    if !(1..=10).contains(&declared) {
        return Err(ParseError::Unclassified);
    }
    let Some((label, rest)) = tail.split_at_checked(usize::from(declared)) else {
        return Err(ParseError::Unclassified);
    };
    let [value] = rest else {
        return Err(ParseError::Unclassified);
    };
    let label = std::str::from_utf8(label).map_err(|_| ParseError::Unclassified)?;
    let kind = match value {
        1 => Kind::One,
        2 => Kind::Two,
        3 => Kind::Three,
        _ => return Err(ParseError::Unclassified),
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
    fn baseline_refusals_are_intentionally_combined() {
        for input in [
            &[][..],
            &[0, 1],
            &[255],
            &[3, 99, 97],
            &[1, 255, 1],
            &[1, 97, 9],
            &[1, 97, 1, 0],
        ] {
            assert_eq!(parse_record(input), Err(ParseError::Unclassified));
        }
    }
}
