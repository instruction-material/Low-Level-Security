fn main() {
    let mut values = [1_u8, 2];
    let first = &mut values[0];
    let second = &mut values[1];
    *first += 1;
    *second += 10;
    println!("{values:?}");
}
