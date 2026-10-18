fn main() {
    let start = std::env::args().count() + 2;
    let values = [10_u8, 20, 30];
    println!("{:?}", &values[start..1]);
}
