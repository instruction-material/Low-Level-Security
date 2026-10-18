pub fn select(name: &str) -> Option<&'static [u8]> {
    match name {
        "cat" => Some(&[3, 99, 97, 116, 1]),
        "empty-label" => Some(&[0, 1]),
        "over-label" => Some(&[11, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 1]),
        "short" => Some(&[3, 99, 97]),
        "utf8" => Some(&[3, 255, 255, 255, 1]),
        "kind" => Some(&[3, 99, 97, 116, 9]),
        "trailing" => Some(&[3, 99, 97, 116, 1, 0]),
        "declared-max" => Some(&[255]),
        "empty" => Some(&[]),
        "missing-kind" => Some(&[1, 97]),
        "length-only" => Some(&[11]),
        "unicode" => Some(&[3, 0xe2, 0x98, 0x83, 2]),
        "exact-max" => Some(&[10, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 3]),
        "combined" => Some(&[1, 255, 9, 0]),
        _ => None,
    }
}
