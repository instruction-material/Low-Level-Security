#![deny(unsafe_op_in_unsafe_fn)]

unsafe fn inspect(pointer: *const u8) -> u8 {
    *pointer
}

fn main() {
    let value = 7;
    // SAFETY: value is live and initialized through this synchronous read.
    println!("{}", unsafe { inspect(&value) });
}
