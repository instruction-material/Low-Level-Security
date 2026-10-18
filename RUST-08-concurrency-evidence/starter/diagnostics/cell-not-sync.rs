use std::cell::Cell;

fn main() {
    let value = Cell::new(7);
    std::thread::scope(|scope| {
        scope.spawn(|| value.set(8));
    });
}
