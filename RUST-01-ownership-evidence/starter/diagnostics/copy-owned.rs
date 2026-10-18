#[derive(Clone, Copy)]
struct Owned {
    label: String,
}

fn main() {
    let first = Owned {
        label: String::from("packet-42"),
    };
    let second = first;
    println!("{}|{}", first.label, second.label);
}
