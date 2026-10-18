// Miri-only rejected case. Do not execute this as a native program.
fn main() {
    let saved = Box::into_raw(Box::new(7_u8));
    // SAFETY: this is the original pointer from Box::into_raw, reconstructed once.
    unsafe { drop(Box::from_raw(saved)) };
    // DELIBERATE VIOLATION: the allocation is freed. Miri must reject this read.
    let observed = unsafe { *saved };
    println!("observed={observed}");
}
