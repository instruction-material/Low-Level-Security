#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WindowError {
    Reversed,
    OutOfBounds,
    NotCharBoundary,
}

impl WindowError {
    pub fn code(self) -> &'static str {
        match self {
            Self::Reversed => "range-reversed",
            Self::OutOfBounds => "out-of-bounds",
            Self::NotCharBoundary => "not-character-boundary",
        }
    }
}

pub fn is_label_char(character: char) -> bool {
    character.is_ascii_alphanumeric() || character == '-'
}

pub fn sanitize(input: &str) -> String {
    input
        .chars()
        .filter(|character| is_label_char(*character))
        .collect()
}

pub fn str_window(input: &str, start: usize, end: usize) -> Result<&str, WindowError> {
    if start > end {
        return Err(WindowError::Reversed);
    }
    if end > input.len() {
        return Err(WindowError::OutOfBounds);
    }
    input.get(start..end).ok_or(WindowError::NotCharBoundary)
}

pub fn byte_window(input: &[u8], start: usize, end: usize) -> Result<&[u8], WindowError> {
    if start > end {
        return Err(WindowError::Reversed);
    }
    input.get(start..end).ok_or(WindowError::OutOfBounds)
}

pub fn char_window(input: &str, start: usize, end: usize) -> Result<&str, WindowError> {
    if start > end {
        return Err(WindowError::Reversed);
    }
    let boundary = |index| {
        input
            .char_indices()
            .map(|(offset, _)| offset)
            .chain(std::iter::once(input.len()))
            .nth(index)
            .ok_or(WindowError::OutOfBounds)
    };
    input
        .get(boundary(start)?..boundary(end)?)
        .ok_or(WindowError::NotCharBoundary)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ascii_predicate_matches_the_exact_label_allowlist() {
        for value in 0_u8..=127 {
            let expected = value.is_ascii_alphanumeric() || value == b'-';
            assert_eq!(is_label_char(char::from(value)), expected);
        }
        for character in ['é', '🦀', 'ß', '\u{301}'] {
            assert!(!is_label_char(character));
        }
    }

    #[test]
    fn valid_label_input_and_empty_input_remain_unchanged() {
        for input in ["", "packet-42", "A-Z-a-z-0-9", "---"] {
            assert_eq!(sanitize(input), input);
        }
    }

    #[test]
    fn filter_removes_every_disallowed_character() {
        assert_eq!(sanitize("packet-42! é🦀_"), "packet-42");
    }

    #[test]
    fn byte_and_string_windows_have_different_boundary_rules() {
        let input = "a🦀bc";
        assert_eq!(input.len(), 7);
        assert_eq!(input.chars().count(), 4);
        assert_eq!(str_window(input, 1, 5).unwrap(), "🦀");
        assert_eq!(str_window(input, 2, 3), Err(WindowError::NotCharBoundary));
        assert_eq!(byte_window(input.as_bytes(), 2, 3).unwrap(), [159]);
    }

    #[test]
    fn error_precedence_and_empty_windows_are_explicit() {
        assert_eq!(str_window("é", 9, 1), Err(WindowError::Reversed));
        assert_eq!(str_window("é", 1, 9), Err(WindowError::OutOfBounds));
        assert_eq!(str_window("é", 1, 1), Err(WindowError::NotCharBoundary));
        assert_eq!(str_window("é", 2, 2).unwrap(), "");
        assert_eq!(str_window("", 0, 0).unwrap(), "");
        assert_eq!(byte_window(&[], 0, 0).unwrap(), []);
    }

    #[test]
    fn scalar_positions_are_not_byte_offsets_or_graphemes() {
        assert_eq!(char_window("é🦀A", 1, 2).unwrap(), "🦀");
        assert_eq!(char_window("e\u{301}", 0, 1).unwrap(), "e");
        assert_eq!(char_window("e\u{301}", 1, 2).unwrap(), "\u{301}");
        assert_eq!(char_window("é", 1, 0), Err(WindowError::Reversed));
        assert_eq!(char_window("é", 0, 2), Err(WindowError::OutOfBounds));
        assert_eq!(char_window("é", 1, 1).unwrap(), "");
    }

    #[test]
    fn every_small_range_preserves_its_declared_index_unit() {
        for input in ["", "packet-42!", "é", "a🦀bc", "e\u{301}", "é\0A"] {
            for start in 0..=input.len() + 2 {
                for end in 0..=input.len() + 2 {
                    let bytes = byte_window(input.as_bytes(), start, end);
                    let text = str_window(input, start, end);
                    let scalar = char_window(input, start, end);
                    if start > end {
                        assert_eq!(bytes, Err(WindowError::Reversed));
                        assert_eq!(text, Err(WindowError::Reversed));
                        assert_eq!(scalar, Err(WindowError::Reversed));
                    } else {
                        assert_eq!(bytes.ok(), input.as_bytes().get(start..end));
                        assert_eq!(text.ok(), input.get(start..end));
                        if end <= input.chars().count() {
                            let expected: String = input.chars().skip(start).take(end - start).collect();
                            assert_eq!(scalar.unwrap(), expected);
                        } else {
                            assert_eq!(scalar, Err(WindowError::OutOfBounds));
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn extreme_ranges_return_errors_without_panicking() {
        assert_eq!(str_window("a", 0, usize::MAX), Err(WindowError::OutOfBounds));
        assert_eq!(byte_window(b"a", usize::MAX, 0), Err(WindowError::Reversed));
        assert_eq!(char_window("a", usize::MAX, usize::MAX), Err(WindowError::OutOfBounds));
        assert_eq!(WindowError::Reversed.code(), "range-reversed");
        assert_eq!(WindowError::OutOfBounds.code(), "out-of-bounds");
        assert_eq!(WindowError::NotCharBoundary.code(), "not-character-boundary");
    }
}
