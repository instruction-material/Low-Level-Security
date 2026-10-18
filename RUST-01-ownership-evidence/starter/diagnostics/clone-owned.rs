#[derive(Clone)]
struct Owned {
    label: String,
}

fn main() {
    let first = Owned {
        label: String::from("packet-42"),
    };
    let mut second = first.clone();
    second.label.push('!');
    println!("{}|{}", first.label, second.label);
}
