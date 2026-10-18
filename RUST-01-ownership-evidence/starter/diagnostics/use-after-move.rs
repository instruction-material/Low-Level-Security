fn consume(label: String) {
    println!("{label}");
}

fn main() {
    let label = String::from("packet-42");
    consume(label);
    println!("{label}");
}
