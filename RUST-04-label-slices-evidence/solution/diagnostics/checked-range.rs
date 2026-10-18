fn main() {
    let start = std::env::args().count() + 2;
    println!("{:?}", [10_u8, 20, 30].get(start..1));
}
