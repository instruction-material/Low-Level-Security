fn digits(input: &str) -> Result<&str, &'static str> {
    let value = input.strip_prefix("A:").ok_or("missing-kind")?;
    Ok(value)
}

fn main() {
    println!("{:?}", digits("B:17"));
}
