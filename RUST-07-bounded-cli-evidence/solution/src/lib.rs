use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::Path;

pub const INPUT_LIMIT: usize = 64;
pub const ROW_LIMIT: usize = 8;
pub const USAGE: &str = "usage: bounded_cli_lab --help | --file NAME.txt\n";

#[derive(Debug, PartialEq, Eq)]
pub enum Error {
    Usage,
    MissingFile,
    NotRegular,
    Read,
    TooLarge,
    InvalidUtf8,
    TooManyRows,
    Record { line: usize, kind: &'static str },
}

impl Error {
    pub fn status(&self) -> u8 {
        match self {
            Self::Usage => 64,
            Self::MissingFile | Self::NotRegular => 66,
            Self::Read => 74,
            _ => 65,
        }
    }

    pub fn diagnostic(&self) -> String {
        match self {
            Self::Usage => USAGE.to_owned(),
            Self::MissingFile => "error=read kind=not-found\n".to_owned(),
            Self::NotRegular => "error=read kind=not-regular\n".to_owned(),
            Self::Read => "error=read kind=io\n".to_owned(),
            Self::TooLarge => "error=input kind=too-large limit=64\n".to_owned(),
            Self::InvalidUtf8 => "error=input kind=invalid-utf8\n".to_owned(),
            Self::TooManyRows => "error=input kind=too-many-rows limit=8\n".to_owned(),
            Self::Record { line, kind } => format!("error=record line={line} kind={kind}\n"),
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum Arguments {
    Help,
    File(String),
}

pub fn valid_fixture_name(name: &str) -> bool {
    let Some(stem) = name.strip_suffix(".txt") else {
        return false;
    };
    !stem.is_empty()
        && name.len() <= 32
        && stem
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-' || byte == b'_')
}

pub fn parse_arguments(arguments: &[OsString]) -> Result<Arguments, Error> {
    match arguments {
        [one] if one == "--help" => Ok(Arguments::Help),
        [mode, name] if mode == "--file" => {
            let name = name.to_str().ok_or(Error::Usage)?;
            if valid_fixture_name(name) {
                Ok(Arguments::File(name.to_owned()))
            } else {
                Err(Error::Usage)
            }
        }
        _ => Err(Error::Usage),
    }
}

pub fn acquire<R: Read>(reader: R) -> Result<Vec<u8>, Error> {
    let mut bytes = Vec::new();
    reader
        .take((INPUT_LIMIT + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|_| Error::Read)?;
    if bytes.len() > INPUT_LIMIT {
        return Err(Error::TooLarge);
    }
    Ok(bytes)
}

fn file_error(error: io::Error) -> Error {
    if error.kind() == io::ErrorKind::NotFound {
        Error::MissingFile
    } else {
        Error::Read
    }
}

pub fn load_fixture(name: &str) -> Result<Vec<u8>, Error> {
    if !valid_fixture_name(name) {
        return Err(Error::Usage);
    }
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("fixtures")
        .join(name);
    let metadata = fs::symlink_metadata(&path).map_err(file_error)?;
    if !metadata.file_type().is_file() {
        return Err(Error::NotRegular);
    }
    let file = File::open(&path).map_err(file_error)?;
    acquire(file)
}

#[derive(Debug, PartialEq, Eq)]
pub struct Record<'a> {
    pub label: &'a str,
    pub value: u16,
}

pub fn decode(bytes: &[u8]) -> Result<&str, Error> {
    if bytes.len() > INPUT_LIMIT {
        return Err(Error::TooLarge);
    }
    std::str::from_utf8(bytes).map_err(|_| Error::InvalidUtf8)
}

pub fn parse_record(text: &str, line: usize) -> Result<Record<'_>, Error> {
    let error = |kind| Error::Record { line, kind };
    let (label, number) = text
        .split_once('=')
        .ok_or_else(|| error("missing-separator"))?;
    if label.is_empty()
        || label.len() > 16
        || !label
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
    {
        return Err(error("invalid-label"));
    }
    if number.is_empty() || !number.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(error("invalid-number"));
    }
    let value = number
        .parse::<u16>()
        .map_err(|_| error("value-out-of-range"))?;
    Ok(Record { label, value })
}

pub fn parse_records(text: &str) -> Result<Vec<Record<'_>>, Error> {
    text.split_terminator('\n')
        .enumerate()
        .map(|(index, text)| {
            if index == ROW_LIMIT {
                Err(Error::TooManyRows)
            } else {
                parse_record(text, index + 1)
            }
        })
        .collect()
}

pub fn summarize(records: &[Record<'_>]) -> (usize, u32) {
    (
        records.len(),
        records.iter().map(|record| u32::from(record.value)).sum(),
    )
}

pub fn render(records: &[Record<'_>]) -> String {
    let (count, total) = summarize(records);
    let labels = if records.is_empty() {
        "-".to_owned()
    } else {
        records
            .iter()
            .map(|record| record.label)
            .collect::<Vec<_>>()
            .join("|")
    };
    format!("count={count} total={total} labels={labels}\n")
}

pub fn process(bytes: &[u8]) -> Result<String, Error> {
    let text = decode(bytes)?;
    let records = parse_records(text)?;
    Ok(render(&records))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn valid_empty_duplicate_and_order_contract() {
        assert_eq!(process(b""), Ok("count=0 total=0 labels=-\n".to_owned()));
        assert_eq!(
            process(b"beta=2\nalpha=7\nbeta=3\n"),
            Ok("count=3 total=12 labels=beta|alpha|beta\n".to_owned())
        );
    }
    #[test]
    fn exact_cap_and_one_over_are_different() {
        let mut exact = b"a=".to_vec();
        exact.extend(vec![b'0'; 61]);
        exact.push(b'1');
        assert_eq!(exact.len(), INPUT_LIMIT);
        assert_eq!(process(&exact), Ok("count=1 total=1 labels=a\n".to_owned()));
        exact.push(b'0');
        assert_eq!(process(&exact), Err(Error::TooLarge));
    }
    #[test]
    fn reading_stops_after_the_single_overflow_probe() {
        let mut source = Cursor::new(vec![b'x'; 4096]);
        assert_eq!(acquire(&mut source), Err(Error::TooLarge));
        assert_eq!(source.position(), 65);
    }
    struct Short {
        source: Cursor<Vec<u8>>,
    }
    impl Read for Short {
        fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
            let count = buffer.len().min(2);
            self.source.read(&mut buffer[..count])
        }
    }
    #[test]
    fn short_reads_do_not_become_false_end_of_input() {
        let value = b"alpha=7\nbeta=17\n".to_vec();
        assert_eq!(
            acquire(Short {
                source: Cursor::new(value.clone())
            }),
            Ok(value)
        );
    }
    struct Broken;
    impl Read for Broken {
        fn read(&mut self, _: &mut [u8]) -> io::Result<usize> {
            Err(io::Error::other("fictional private detail"))
        }
    }
    #[test]
    fn read_failures_do_not_echo_private_io_details() {
        let error = acquire(Broken).expect_err("reader fails");
        assert_eq!(error, Error::Read);
        assert_eq!(error.diagnostic(), "error=read kind=io\n");
        assert_eq!(error.status(), 74);
    }
    #[test]
    fn byte_cap_precedes_utf8_and_utf8_precedes_records() {
        assert_eq!(process(&[0xff; 65]), Err(Error::TooLarge));
        assert_eq!(process(b"bad\n\xff"), Err(Error::InvalidUtf8));
    }
    #[test]
    fn line_and_field_error_priority_is_explicit() {
        assert_eq!(
            process(b"alpha=7\n=no\n"),
            Err(Error::Record {
                line: 2,
                kind: "invalid-label"
            })
        );
        assert_eq!(
            process(b"a=65536x"),
            Err(Error::Record {
                line: 1,
                kind: "invalid-number"
            })
        );
        assert_eq!(
            process(b"a=65536"),
            Err(Error::Record {
                line: 1,
                kind: "value-out-of-range"
            })
        );
    }
    #[test]
    fn blank_crlf_and_extra_equals_are_not_normalized() {
        for bytes in [b"\n".as_slice(), b"a=1\r\n", b"a=1=2", b"a=1\n\n"] {
            assert!(process(bytes).is_err());
        }
    }
    #[test]
    fn row_limit_is_checked_before_the_ninth_record() {
        let mut input = "a=0\n".repeat(8);
        assert!(process(input.as_bytes()).is_ok());
        input.push_str("bad");
        assert_eq!(process(input.as_bytes()), Err(Error::TooManyRows));
    }
    #[test]
    fn names_and_arguments_exclude_path_syntax() {
        for name in [
            "../valid.txt",
            "/valid.txt",
            "folder/valid.txt",
            "a\\b.txt",
            ".txt",
            "a.b.txt",
            "c:valid.txt",
        ] {
            assert!(!valid_fixture_name(name));
        }
        assert!(valid_fixture_name("cap-1_ok.txt"));
        assert_eq!(parse_arguments(&["--help".into()]), Ok(Arguments::Help));
        assert_eq!(
            parse_arguments(&["--file".into(), "valid.txt".into()]),
            Ok(Arguments::File("valid.txt".to_owned()))
        );
        assert_eq!(parse_arguments(&[]), Err(Error::Usage));
    }
}
