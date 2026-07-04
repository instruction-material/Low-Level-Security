const ALLOWED_SEPARATOR: char = '-';
const SAMPLE_INPUT: &str = "packet-42!";

/// Remove characters that are not allowed in packet labels
fn sanitize(input: &str) -> String {
	// Keep alphanumeric characters and the allowed separator
	input
		.chars()
		.filter(|character| character.is_ascii_alphanumeric() || *character == ALLOWED_SEPARATOR)
		.collect()
}

/// Print the sanitized sample label
fn main() {
	println!("{}", sanitize(SAMPLE_INPUT));
}
