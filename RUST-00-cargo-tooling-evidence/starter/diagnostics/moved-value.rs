fn main() {
    let label = String::from("packet-42");
    let moved = label;
    println!("{moved}");
    println!("{label}");
}
