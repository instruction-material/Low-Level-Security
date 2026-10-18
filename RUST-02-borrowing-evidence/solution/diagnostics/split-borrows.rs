fn main() {
    let mut values = [1_u8, 2];
    let (left, right) = values.split_at_mut(1);
    left[0] += 1;
    right[0] += 10;
    println!("{values:?}");
}
