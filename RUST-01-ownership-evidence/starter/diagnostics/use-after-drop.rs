fn main() {
    let label = String::from("packet-42");
    drop(label);
    println!("{label}");
}
