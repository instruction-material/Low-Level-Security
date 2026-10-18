fn main() {
    let label = String::from("packet-42");
    println!("{label}");
    drop(label);
}
