fn main() {
    let mut owner = String::from("ALPHA");
    let label = &owner;
    println!("{label}");
    owner.make_ascii_lowercase();
    println!("{owner}");
}
