#![forbid(unsafe_code)]

pub fn parse_record(input: &str) -> i32 {
    let (kind, value) = match input.split_once(':') {
        Some(parts) => parts,
        None => return -1,
    };
    if kind != "A" {
        return -2;
    }
    if value.is_empty() {
        return -3;
    }
    if !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return -4;
    }
    match value.parse::<u16>() {
        Ok(value) => i32::from(value),
        Err(_) => -5,
    }
}

pub fn first_record(rows: &[&str]) -> (usize, i32) {
    for (index, row) in rows.iter().enumerate() {
        if !row.is_empty() {
            return (index, parse_record(row));
        }
    }
    (usize::MAX, 0)
}

pub fn all_records(rows: &[&str]) -> Vec<(usize, i32)> {
    rows.iter()
        .enumerate()
        .filter(|(_, row)| !row.is_empty())
        .map(|(index, row)| (index, parse_record(row)))
        .collect()
}

pub fn public_error(code: i32) -> Option<(&'static str, &'static str)> {
    match code {
        -1 => Some(("missing-separator", "add-separator")),
        -2 => Some(("unknown-kind", "choose-A")),
        -3 => Some(("missing-value", "supply-value")),
        -4 => Some(("invalid-number", "use-ASCII-digits")),
        -5 => Some(("value-out-of-range", "use-u16-range")),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_every_u16_value() {
        for value in 0..=u16::MAX {
            assert_eq!(parse_record(&format!("A:{value}")), i32::from(value));
        }
    }

    #[test]
    fn keeps_five_error_classes_distinct() {
        let cases = [
            ("A17", -1),
            ("B:17", -2),
            ("A:", -3),
            ("A:x", -4),
            ("A:65536", -5),
        ];
        for (input, code) in cases {
            assert_eq!(parse_record(input), code);
        }
    }

    #[test]
    fn accepts_leading_zeros_without_a_false_width_limit() {
        assert_eq!(parse_record("A:00017"), 17);
        assert_eq!(parse_record("A:0000065535"), 65535);
        assert_eq!(parse_record(&format!("A:{}65535", "0".repeat(96))), 65535);
    }

    #[test]
    fn rejects_extra_separators_whitespace_unicode_and_nul() {
        for input in ["A:17:2", "A:17 ", "A: 17", "A:+17", "A:١٧", "A:1\0"] {
            assert_eq!(parse_record(input), -4);
        }
    }

    #[test]
    fn absence_is_not_the_valid_zero_record() {
        assert_eq!(first_record(&[]), (usize::MAX, 0));
        assert_eq!(first_record(&["", ""]), (usize::MAX, 0));
        assert_eq!(first_record(&["", "A:0"]), (1, 0));
    }

    #[test]
    fn first_candidate_retains_context_and_does_not_skip_errors() {
        assert_eq!(first_record(&["", "A:", "A:17"]), (1, -3));
        assert_eq!(first_record(&["A:17", "B:0"]), (0, 17));
    }

    #[test]
    fn collection_keeps_successes_and_indexed_errors() {
        let expected = vec![(1, 17), (2, -2), (3, 0)];
        assert_eq!(all_records(&["", "A:17", "B:0", "A:0"]), expected);
    }

    #[test]
    fn public_actions_are_distinct_and_do_not_echo_input() {
        let mut actions = Vec::new();
        for code in [-1, -2, -3, -4, -5] {
            let Some((message, action)) = public_error(code) else {
                panic!("the baseline contract defines these five codes");
            };
            assert!(!message.contains("PRIVATE_MARKER"));
            actions.push(action);
        }
        actions.sort_unstable();
        actions.dedup();
        assert_eq!(actions.len(), 5);
        assert_eq!(public_error(17), None);
    }
}
