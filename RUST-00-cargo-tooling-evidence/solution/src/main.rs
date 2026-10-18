use std::process::ExitCode;

fn normalize_label(input: &str) -> String {
    input
        .chars()
        .filter(|character| character.is_ascii_alphanumeric() || *character == '-')
        .collect()
}

fn main() -> ExitCode {
    let mut arguments = std::env::args_os().skip(1);
    let input = match arguments.next() {
        Some(value) => match value.into_string() {
            Ok(text) => text,
            Err(_) => {
                eprintln!("label must be valid UTF-8");
                return ExitCode::from(64);
            }
        },
        None => "packet-42!".to_owned(),
    };
    if arguments.next().is_some() {
        eprintln!("usage: cargo_tooling_lab [label]");
        return ExitCode::from(64);
    }
    println!("{}", normalize_label(&input));
    ExitCode::SUCCESS
}

#[cfg(test)]
mod tests {
    use super::normalize_label;

    #[test]
    fn documented_examples() {
        for (input, expected) in [
            ("packet-42!", "packet-42"),
            ("A B_c/9", "ABc9"),
            ("", ""),
            ("---", "---"),
            ("café-42", "caf-42"),
            ("🦀", ""),
            ("../etc/passwd", "etcpasswd"),
        ] {
            assert_eq!(normalize_label(input), expected);
        }
    }

    #[test]
    fn every_ascii_character_has_the_declared_outcome() {
        for byte in 0_u8..=127 {
            let character = char::from(byte);
            let output = normalize_label(&character.to_string());
            let expected = if character.is_ascii_alphanumeric() || character == '-' {
                character.to_string()
            } else {
                String::new()
            };
            assert_eq!(output, expected);
        }
    }

    #[test]
    fn normalizing_twice_preserves_the_first_result() {
        let original = "AB-0 café / ../🦀";
        let once = normalize_label(original);
        assert_eq!(normalize_label(&once), once);
    }
}
