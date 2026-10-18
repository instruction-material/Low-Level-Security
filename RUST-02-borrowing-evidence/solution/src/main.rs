#![forbid(unsafe_code)]

use std::process::ExitCode;

#[derive(Debug, PartialEq, Eq)]
struct RecordView<'a> {
    name: &'a str,
    role: &'a str,
}

fn parse_record(input: &str) -> Result<RecordView<'_>, &'static str> {
    let (left, right) = input.split_once(';').ok_or("invalid record")?;
    let name = left.strip_prefix("name=").ok_or("invalid record")?;
    let role = right.strip_prefix("role=").ok_or("invalid record")?;
    if role.contains(';') {
        return Err("invalid record");
    }
    Ok(RecordView { name, role })
}

fn normalize_ascii(value: &mut str) {
    value.make_ascii_lowercase();
}

fn longer<'a>(left: &'a str, right: &'a str) -> &'a str {
    if left.len() >= right.len() {
        left
    } else {
        right
    }
}

fn bump_halves(values: &mut [u8]) {
    let midpoint = values.len() / 2;
    let (left, right) = values.split_at_mut(midpoint);
    for value in left {
        *value = value.wrapping_add(1);
    }
    for value in right {
        *value = value.wrapping_add(10);
    }
}

fn owned_result(label: &str) -> String {
    label.to_owned()
}

fn main() -> ExitCode {
    let mut args = std::env::args_os().skip(1);
    let mut record = match args.next() {
        None => String::from("name=ALPHA;role=ADMIN"),
        Some(value) => match value.into_string() {
            Ok(text) => text,
            Err(_) => {
                eprintln!("record must be valid UTF-8");
                return ExitCode::from(64);
            }
        },
    };
    let mut counters = match args.next() {
        None => vec![1, 2, 3, 4],
        Some(value) if value == "full" => vec![1, 2, 3, 4],
        Some(value) if value == "empty" => Vec::new(),
        Some(_) => {
            eprintln!("usage: borrowed_record_lab [record [full|empty]]");
            return ExitCode::from(64);
        }
    };
    if args.next().is_some() {
        eprintln!("usage: borrowed_record_lab [record [full|empty]]");
        return ExitCode::from(64);
    }
    let view = match parse_record(&record) {
        Ok(view) => view,
        Err(_) => {
            eprintln!("expected name=<text>;role=<text> with exactly two fields");
            return ExitCode::from(65);
        }
    };
    println!("shared={}|{}", view.name, view.role);
    normalize_ascii(record.as_mut_str());
    let normalized = parse_record(&record).expect("ASCII case preserves the record schema");
    println!("normalized={record}");
    println!("selected={}", longer(normalized.name, normalized.role));
    let name = owned_result(normalized.name);
    bump_halves(&mut counters);
    println!("halves={counters:?}");
    drop(record);
    println!("owned-after-drop={name}");
    ExitCode::SUCCESS
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parser_preserves_empty_fields_unicode_and_equals() {
        let empty = parse_record("name=;role=").unwrap();
        assert!(empty.name.is_empty() && empty.role.is_empty());
        let view = parse_record("name=ÉA;role=ROLE=VALUE").unwrap();
        assert_eq!(view.name, "ÉA");
        assert_eq!(view.role, "ROLE=VALUE");
    }

    #[test]
    fn parser_rejects_missing_reordered_and_extra_fields() {
        for text in [
            "name=a",
            "name=a;group=b",
            "name=a;role=b;extra=c",
            "NAME=a;role=b",
        ] {
            assert!(parse_record(text).is_err());
        }
    }

    #[test]
    fn ascii_normalization_preserves_utf8_and_byte_length() {
        let mut text = String::from("name=ÉA;role=Crab🦀");
        let length = text.len();
        normalize_ascii(text.as_mut_str());
        assert_eq!(text, "name=Éa;role=crab🦀");
        assert_eq!(text.len(), length);
    }

    #[test]
    fn longer_uses_byte_length_and_keeps_left_ties() {
        let left = String::from("alpha");
        let right = String::from("bravo");
        assert!(std::ptr::eq(longer(&left, &right).as_ptr(), left.as_ptr()));
        assert_eq!(longer("🦀", "abc"), "🦀");
        assert_eq!(longer("a", "long"), "long");
        assert_eq!(longer("", ""), "");
    }

    #[test]
    fn disjoint_halves_cover_empty_odd_and_wrapping_values() {
        let mut empty = [];
        bump_halves(&mut empty);
        let mut one = [255];
        bump_halves(&mut one);
        assert_eq!(one, [9]);
        let mut three = [255, 250, 0];
        bump_halves(&mut three);
        assert_eq!(three, [0, 4, 10]);
        let mut four = [1, 2, 3, 4];
        bump_halves(&mut four);
        assert_eq!(four, [2, 3, 13, 14]);
    }

    #[test]
    fn deliberate_owned_result_survives_the_input_owner() {
        let name;
        {
            let record = String::from("name=alpha;role=admin");
            let view = parse_record(&record).unwrap();
            name = owned_result(view.name);
        }
        assert_eq!(name, "alpha");
    }

    #[test]
    fn borrowed_view_points_into_the_input_fields() {
        let record = String::from("name=alpha;role=admin");
        let view = parse_record(&record).unwrap();
        assert!(std::ptr::eq(view.name.as_ptr(), record[5..].as_ptr()));
        assert!(std::ptr::eq(view.role.as_ptr(), record[16..].as_ptr()));
    }
}
