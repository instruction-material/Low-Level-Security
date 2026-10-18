use std::sync::Arc;

fn main() {
    let value = Arc::new(7);
    std::thread::spawn(move || println!("{}", *value))
        .join()
        .unwrap();
}
