fn main() {
    let value = 7;
    std::thread::scope(|scope| {
        scope.spawn(|| println!("{value}")).join().unwrap();
    });
}
