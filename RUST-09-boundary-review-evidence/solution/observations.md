# Reference boundary review

## CORE
The safe oracle caps input at eight bytes. Empty sums to zero; [7,17] sums to 24;
eight 255 bytes sum to 2040. A ninth byte is rejected before pointer conversion.
The local ABI is supplied for contract review; pure Rust summation needs no FFI.
Source pointers and output pointers remain inside the private bridge.

## WORKFLOW
The input slice remains borrowed through the call and the output is a distinct
initialized u32 local. The fixed raw_sum must not retain, free or mutate input,
overrun output or unwind. Nonempty slice construction depends on the live,
initialized, single-allocation input contract. Empty input avoids a null slice.
Null refusal tests are guarded paths, not validation of arbitrary non-null
addresses. The reference maps status 64 to Rejected and unknown statuses to
Protocol. Missing writes and impossible sums are caught by the initialized
sentinel and range check. Retain actual commands and a separate regression.

## CHOICE
The private test seam returns defined refusal, unknown status, success without
writing, and success with 2041. It obeys memory-safety obligations while violating
the logical protocol. A plausible wrong sum would pass the range check, so
compare it with safe_checksum. A malicious write could cause UB before any
status check; this reference does not claim to contain an arbitrary callee.

## CHALLENGE
E0133 distinguishes calling an unsafe function without a block from performing
an unchecked operation inside an unsafe function under deny(unsafe_op_in_unsafe_fn).
Both explicit alternatives retain the same live-byte precondition. The Miri-only
case reconstructs and drops its Box exactly once, then deliberately reads the
freed allocation. Use the recorded Miri evidence in README or run the bounded
experiment; never treat a native value from that case as valid evidence.

## LIMITS
This is a local Rust implementation of a C ABI, not a tested foreign C library.
No raw pointer, backend selection or exported symbol is exposed by the public
Rust API. The compiler checks types; the ledger, independent corpus and Miri
evidence address different contracts and do not prove every target or execution.
