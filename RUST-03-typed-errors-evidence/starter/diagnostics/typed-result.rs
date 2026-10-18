fn value() -> Result<u16, &'static str> {
    Err("missing-value")
}

fn main() {
    println!("{:?}", value());
}
