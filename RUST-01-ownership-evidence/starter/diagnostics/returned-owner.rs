fn relay(label: String) -> String {
    label
}

fn main() {
    let label = String::from("packet-42");
    let label = relay(label);
    println!("{label}");
}
