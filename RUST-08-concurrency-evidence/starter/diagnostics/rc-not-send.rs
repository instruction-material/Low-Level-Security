use std::rc::Rc;

fn main() {
    let value = Rc::new(7);
    std::thread::spawn(move || println!("{}", *value)).join().unwrap();
}
