//! A private Rust implementation of the supplied C calling convention.
use crate::MAX_BYTES;

/// Review stand-in: status 0 writes the sum; status 64 writes nothing.
///
/// # Safety
/// Arguments refused by the initial length/null guard require no memory access.
/// Otherwise, for len > 0, data must designate len initialized,
/// readable bytes within one live allocation, unchanged throughout this call.
/// On a non-refused call, output must be aligned, writable for one u32, live,
/// and disjoint from the input. Neither pointer is retained or freed here.
/// Null output, null data with nonzero len, and len > 8 are guarded refusals;
/// they require no dereference. A null data pointer is accepted only for len 0.
pub(super) unsafe extern "C" fn raw_sum(data: *const u8, len: usize, output: *mut u32) -> i32 {
    if len > MAX_BYTES || output.is_null() || (len != 0 && data.is_null()) {
        return 64;
    }
    let bytes = if len == 0 {
        &[]
    } else {
        // SAFETY: the caller provides one live initialized allocation for len
        // immutable bytes; len <= 8 also satisfies the slice size bound.
        unsafe { std::slice::from_raw_parts(data, len) }
    };
    let sum = bytes.iter().map(|value| u32::from(*value)).sum();
    // SAFETY: a non-null output is aligned, live, writable and disjoint from
    // the borrowed input by the caller contract. u32 requires no destructor.
    unsafe { output.write(sum) };
    0
}

#[cfg(test)]
mod raw_tests {
    use super::*;

    #[test]
    fn valid_borrowed_storage_and_separate_output() {
        let bytes = [7, 17];
        let mut output = u32::MAX;
        // SAFETY: the byte array and distinct aligned output live through the call.
        assert_eq!(
            unsafe { raw_sum(bytes.as_ptr(), bytes.len(), &mut output) },
            0
        );
        assert_eq!(output, 24);
    }

    #[test]
    fn null_empty_input_is_handled_without_making_a_null_slice() {
        let mut output = u32::MAX;
        // SAFETY: null input with len 0 is explicitly supported; output is valid.
        assert_eq!(unsafe { raw_sum(std::ptr::null(), 0, &mut output) }, 0);
        assert_eq!(output, 0);
    }

    #[test]
    fn null_nonempty_input_is_a_guarded_refusal() {
        let mut output = 123;
        // SAFETY: this null-input refusal is defined to occur before dereference.
        assert_eq!(unsafe { raw_sum(std::ptr::null(), 1, &mut output) }, 64);
        assert_eq!(output, 123);
    }

    #[test]
    fn null_output_is_a_guarded_refusal() {
        let bytes = [7];
        // SAFETY: null output is explicitly guarded; the input is live and readable.
        assert_eq!(
            unsafe { raw_sum(bytes.as_ptr(), 1, std::ptr::null_mut()) },
            64
        );
    }

    #[test]
    fn oversized_length_is_checked_before_reading_the_small_array() {
        let bytes = [7];
        let mut output = 123;
        // SAFETY: len > 8 is a guarded refusal and no input/output is accessed.
        assert_eq!(unsafe { raw_sum(bytes.as_ptr(), 9, &mut output) }, 64);
        assert_eq!(output, 123);
    }
}
