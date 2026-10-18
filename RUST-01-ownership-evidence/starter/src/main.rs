#![forbid(unsafe_code)]

use std::process::ExitCode;

#[derive(Clone, Debug, PartialEq, Eq)]
struct Packet {
    label: String,
    bytes: Vec<u8>,
}

fn make_packet(label: String, bytes: Vec<u8>) -> Packet {
    Packet { label, bytes }
}

fn relay(packet: Packet) -> Packet {
    packet
}

fn append_marker(mut bytes: Vec<u8>) -> Vec<u8> {
    bytes.push(9);
    bytes
}

fn add_marker(packet: Packet) -> Packet {
    let Packet { label, bytes } = packet;
    Packet {
        label,
        bytes: append_marker(bytes),
    }
}

fn borrowed_label(packet: &Packet) -> &str {
    &packet.label
}

fn describe(stage: &str, packet: &Packet) -> String {
    format!("{stage}={} bytes={:?}", packet.label, packet.bytes)
}

fn ownership_trace(label: String, bytes: Vec<u8>) -> Vec<String> {
    let id = 7_u32;
    let copied_id = id;
    let packet = make_packet(label, bytes);
    let snapshot = packet.clone();
    let mut lines = vec![
        format!("copy={id},{copied_id}"),
        describe("owned", &packet),
        describe("cloned", &snapshot),
    ];
    let moved = relay(packet);
    let updated = add_marker(moved);
    lines.push(describe("after-edit", &updated));
    lines.push(describe("snapshot", &snapshot));
    lines.push(format!("borrowed-label={}", borrowed_label(&updated)));
    let returned = relay(updated);
    lines.push(describe("returned", &returned));
    lines
}

struct ScopeTag(&'static str);

impl Drop for ScopeTag {
    fn drop(&mut self) {
        println!("drop={}", self.0);
    }
}

fn scope_trace() {
    let _outer = ScopeTag("outer");
    {
        let _first = ScopeTag("inner-first");
        let _second = ScopeTag("inner-second");
    }
    let explicit = ScopeTag("explicit");
    drop(explicit);
    println!("after-explicit-drop");
}

fn main() -> ExitCode {
    let mut args = std::env::args_os().skip(1);
    let label = match args.next() {
        None => String::from("packet-42"),
        Some(value) => match value.into_string() {
            Ok(text) => text,
            Err(_) => {
                eprintln!("label must be valid UTF-8");
                return ExitCode::from(64);
            }
        },
    };
    let bytes = match args.next() {
        None => vec![3, 1, 4],
        Some(value) if value == "default" => vec![3, 1, 4],
        Some(value) if value == "empty" => Vec::new(),
        Some(_) => {
            eprintln!("usage: ownership_trace_lab [label [default|empty]]");
            return ExitCode::from(64);
        }
    };
    if args.next().is_some() {
        eprintln!("usage: ownership_trace_lab [label [default|empty]]");
        return ExitCode::from(64);
    }
    for line in ownership_trace(label, bytes) {
        println!("{line}");
    }
    scope_trace();
    ExitCode::SUCCESS
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn moved_packet_preserves_its_owned_fields() {
        let packet = make_packet(String::from("alpha"), vec![1, 2]);
        let result = add_marker(relay(packet));
        assert_eq!(result.label, "alpha");
        assert_eq!(result.bytes, [1, 2, 9]);
    }

    #[test]
    fn cloned_packet_has_independent_owned_data() {
        let original = make_packet(String::from("alpha"), vec![1, 2]);
        let mut cloned = original.clone();
        cloned.label.push('!');
        cloned.bytes.push(9);
        assert_eq!(original.label, "alpha");
        assert_eq!(original.bytes, [1, 2]);
        assert_eq!(cloned.label, "alpha!");
        assert_eq!(cloned.bytes, [1, 2, 9]);
    }

    #[test]
    fn empty_fields_can_be_moved_and_rebuilt() {
        let packet = make_packet(String::new(), Vec::new());
        let result = add_marker(relay(packet));
        assert_eq!(result.label, "");
        assert_eq!(result.bytes, [9]);
    }

    #[test]
    fn reading_through_a_borrow_does_not_consume_the_packet() {
        let packet = make_packet(String::from("alpha"), vec![1]);
        assert_eq!(borrowed_label(&packet), "alpha");
        let returned = relay(packet);
        assert_eq!(returned.label, "alpha");
    }
}
