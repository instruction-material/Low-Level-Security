#![forbid(unsafe_code)]

use std::cell::Cell;

/// A finite sequence of unchanged row texts, in source order.
pub trait RowSource {
    fn rows(&self) -> impl Iterator<Item = &str>;
}

#[derive(Debug)]
pub struct MemoryRows {
    values: Vec<String>,
    pulls: Cell<usize>,
}

impl MemoryRows {
    pub fn new(values: Vec<String>) -> Self {
        Self {
            values,
            pulls: Cell::new(0),
        }
    }

    pub fn push(&mut self, value: String) {
        self.values.push(value);
    }

    pub fn pulls(&self) -> usize {
        self.pulls.get()
    }

    pub fn reset_pulls(&self) {
        self.pulls.set(0);
    }
}

impl RowSource for MemoryRows {
    fn rows(&self) -> impl Iterator<Item = &str> {
        self.values.iter().map(String::as_str).inspect(|_| {
            self.pulls.set(self.pulls.get() + 1);
        })
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ParseError {
    MissingSeparator,
    InvalidLabel,
    InvalidNumber,
    ValueOutOfRange,
}

impl ParseError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::MissingSeparator => "missing-separator",
            Self::InvalidLabel => "invalid-label",
            Self::InvalidNumber => "invalid-number",
            Self::ValueOutOfRange => "value-out-of-range",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RowError {
    pub index: usize,
    pub kind: ParseError,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Record<'a> {
    pub label: &'a str,
    pub value: u16,
}

pub fn parse_record(text: &str) -> Result<Record<'_>, ParseError> {
    let (label, value) = text.split_once('=').ok_or(ParseError::MissingSeparator)?;
    if label.is_empty()
        || label.len() > 16
        || !label
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
    {
        return Err(ParseError::InvalidLabel);
    }
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ParseError::InvalidNumber);
    }
    let value = value.parse().map_err(|_| ParseError::ValueOutOfRange)?;
    Ok(Record { label, value })
}

#[derive(Debug, PartialEq, Eq)]
pub struct Report<'a> {
    pub labels: Vec<&'a str>,
    pub total: u128,
}

pub struct BorrowedRows<'a> {
    values: &'a [&'a str],
}

impl<'a> BorrowedRows<'a> {
    pub fn new(values: &'a [&'a str]) -> Self {
        Self { values }
    }
}

impl RowSource for BorrowedRows<'_> {
    fn rows(&self) -> impl Iterator<Item = &str> {
        self.values.iter().copied()
    }
}

pub fn audit<S: RowSource>(source: &S) -> Result<Report<'_>, RowError> {
    source.rows().enumerate().try_fold(
        Report {
            labels: Vec::new(),
            total: 0,
        },
        |mut report, (index, text)| {
            let record = parse_record(text).map_err(|kind| RowError {
                index: index + 1,
                kind,
            })?;
            report.labels.push(record.label);
            report.total += u128::from(record.value);
            Ok(report)
        },
    )
}

pub fn all_records<S: RowSource>(source: &S) -> Vec<Result<Record<'_>, RowError>> {
    source
        .rows()
        .enumerate()
        .map(|(index, text)| {
            parse_record(text).map_err(|kind| RowError {
                index: index + 1,
                kind,
            })
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn memory(rows: &[&str]) -> MemoryRows {
        MemoryRows::new(rows.iter().map(|row| (*row).to_owned()).collect())
    }

    #[test]
    fn parser_error_order_is_part_of_the_contract() {
        assert_eq!(parse_record("bad"), Err(ParseError::MissingSeparator));
        assert_eq!(parse_record("=no"), Err(ParseError::InvalidLabel));
        assert_eq!(
            parse_record("bad label=65536x"),
            Err(ParseError::InvalidLabel)
        );
        assert_eq!(parse_record("a=65536x"), Err(ParseError::InvalidNumber));
        assert_eq!(parse_record("a=65536"), Err(ParseError::ValueOutOfRange));
    }

    #[test]
    fn audit_preserves_source_order_duplicates_and_sum() {
        let source = memory(&["beta=0", "alpha=7", "beta=17"]);
        let report = audit(&source).expect("valid rows");
        assert_eq!(report.labels, ["beta", "alpha", "beta"]);
        assert_eq!(report.total, 24);
        assert_eq!(source.pulls(), 3);
    }

    #[test]
    fn fail_fast_reports_first_one_based_error() {
        let source = memory(&["alpha=7", "bad", "=no"]);
        assert_eq!(
            audit(&source),
            Err(RowError {
                index: 2,
                kind: ParseError::MissingSeparator
            })
        );
    }

    #[test]
    fn all_records_preserves_one_outcome_per_input() {
        let source = memory(&["alpha=7", "bad", "beta=17"]);
        let rows = all_records(&source);
        assert_eq!(rows.len(), 3);
        assert_eq!(rows[0].as_ref().expect("first valid").label, "alpha");
        assert_eq!(
            rows[1],
            Err(RowError {
                index: 2,
                kind: ParseError::MissingSeparator
            })
        );
        assert_eq!(rows[2].as_ref().expect("last valid").value, 17);
        assert_eq!(source.pulls(), 3);
    }

    #[test]
    fn empty_inputs_and_parser_boundaries_stay_explicit() {
        let source = memory(&[]);
        let report = audit(&source).expect("empty is valid");
        assert!(report.labels.is_empty());
        assert_eq!(report.total, 0);
        assert!(all_records(&source).is_empty());
        assert_eq!(parse_record("a=00017").expect("leading zeroes").value, 17);
        assert_eq!(parse_record("a=65535").expect("maximum").value, 65535);
        assert_eq!(
            parse_record("abcdefghijklmnop=0").expect("16 bytes").label,
            "abcdefghijklmnop"
        );
        assert_eq!(
            parse_record("abcdefghijklmnopq=0"),
            Err(ParseError::InvalidLabel)
        );
        assert_eq!(parse_record("café=2"), Err(ParseError::InvalidLabel));
        assert_eq!(parse_record("a=+1"), Err(ParseError::InvalidNumber));
    }

    #[test]
    fn ownership_baseline_or_borrowed_target_is_visible() {
        let source = memory(&["alpha=7"]);
        let report = audit(&source).expect("valid");
        assert_eq!(report.labels[0].as_ptr(), source.values[0].as_ptr());
    }

    #[test]
    fn concrete_baseline_or_alternate_source_is_visible() {
        let rows = ["beta=5", "alpha=7"];
        let source = BorrowedRows::new(&rows);
        let report = audit(&source).expect("valid");
        assert_eq!(report.labels, ["beta", "alpha"]);
        assert_eq!(report.total, 12);
        assert_eq!(all_records(&source).len(), 2);
    }

    #[test]
    fn eager_baseline_or_lazy_target_pulls_are_visible() {
        let source = memory(&["alpha=7", "bad", "omega=17"]);
        assert!(audit(&source).is_err());
        assert_eq!(source.pulls(), 2);
        source.reset_pulls();
        assert_eq!(all_records(&source).len(), 3);
        assert_eq!(source.pulls(), 3);
    }
}
