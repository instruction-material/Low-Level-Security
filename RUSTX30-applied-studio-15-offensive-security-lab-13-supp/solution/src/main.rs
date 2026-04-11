fn sanitize(input: &str) -> String {
	input
		.chars()
		.filter(|ch| ch.is_ascii_alphanumeric() || *ch == '-')
		.collect()
}

fn main() {
	println!("{}", sanitize("packet-42!"));
}
