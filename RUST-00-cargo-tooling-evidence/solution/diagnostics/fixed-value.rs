fn inspect(label: &str) {
    println!("{label}");
}

fn main() {
    let label = String::from("packet-42");
    inspect(&label);
    inspect(&label);
}
