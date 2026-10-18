fn main() {
    let mut owner = String::from("ALPHA");
    let label = &owner;
    owner.make_ascii_lowercase();
    println!("{label}");
}
