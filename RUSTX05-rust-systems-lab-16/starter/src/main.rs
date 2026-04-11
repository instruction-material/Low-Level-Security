fn sanitize(input: &str) -> String {
	// TODO: keep only ASCII alphanumeric characters and dashes.
	input.to_string()
}

fn main() {
	println!("{}", sanitize("packet-42!"));
}
