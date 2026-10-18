fn local_label() -> &'static str {
    let local = String::from("alpha");
    local.as_str()
}

fn main() {
    println!("{}", local_label());
}
