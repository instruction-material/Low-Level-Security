fn main() {
    let index = std::env::args().count() + 3;
    println!("{}", [10_u8, 20, 30][index]);
}
