unsafe fn inspect(pointer: *const u8) -> u8 {
    // SAFETY: caller must provide a live initialized byte for this read.
    unsafe { *pointer }
}

fn main() {
    let value = 7;
    println!("{}", inspect(&value));
}
