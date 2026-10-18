# Review a pointer-and-status boundary

The safe baseline adds at most eight bytes into a u32. Review the supplied
private C-ABI stand-in before replacing that baseline with a checked wrapper.
The starter's public checksum stays entirely safe; its raw bridge is compiled
only for tests. The reference enables the private bridge and contains its raw
values behind the same public `checksum(&[u8]) -> Result<u32, BoundaryError>`.
No public Rust function accepts a raw pointer or a caller-selected backend.

The named need is auditing an existing pointer/length/output/status contract.
The stand-in is implemented in Rust with the C calling convention so it needs
no external library. These tests demonstrate the local ABI call and wrapper;
they do not verify a foreign C build, binary compatibility or an actual vendor
library. For ordinary Rust-only summation, keep `safe_checksum` instead.

## Contract and source map

Read src/lib.rs first, then src/bridge.rs. MAX_BYTES is 8. Each input value is
u8, so the largest accepted sum is 2040, safely representable in u32. Empty
input has sum 0. A ninth byte returns TooLarge before an ABI call. The API
returns an owned number; it neither changes input nor returns or retains a
borrow into it. A slice is borrowed initialized storage; a raw pointer carries
no equivalent checked length or lifetime. An unsafe block records a proof
obligation, not a runtime validation of arbitrary memory.

The supplied ABI shape corresponds to a C prototype such as
`int32_t sum(const uint8_t *data, size_t length, uint32_t *output)`.
Do not substitute a Rust Vec, String, reference or enum as an undocumented C
parameter. Target ABI, size_t and unwind behavior need independent agreement
before a real cross-language integration. This case exports no symbol.

raw_sum returns status 0 only after writing a sum, or 64 without writing.
It first refuses length > 8, null output, or null input with nonzero length.
Null input with length 0 uses an existing empty slice; it is never passed to
from_raw_parts. Null checks cannot establish allocation, alignment, provenance,
initialized bytes, aliasing, synchronization or lifetime for a non-null pointer.
Those remain caller obligations. Do not manufacture dangling or misaligned
callers to test the native boundary.

For a nonempty input, the caller must supply initialized readable bytes within
one live allocation, unchanged during the call. A non-null output must be live,
aligned and writable for one u32, disjoint from the input. The callee must not
retain, free or mutate input, overrun either allocation or unwind across this
ABI. These are contracts to inspect, not properties a pointer type proves.

In the reference, checked_sum chooses only the fixed private raw_sum. invoke
checks length, creates a separate initialized stack output and makes the call
while the input borrow remains live. It maps 64 to Rejected and every unknown
status to Protocol. Status 0 is accepted only if the output is <= length × 255.
The initial u32::MAX sentinel makes a missing write a protocol error without
reading uninitialized storage. A malicious callee could still corrupt memory
before returning; checking status or a plausible sum cannot make that safe.
An in-range wrong sum is a semantic defect, tested against the safe baseline.
No panic is expected from this finite, nonallocating byte loop and bounded sum;
extern C is not an agreement to unwind safely. The test backends are fixed,
private, synchronous stand-ins that obey memory safety while violating status
or output semantics. They model a logic failure, not arbitrary foreign code.

## Unsafe ledger

For each row, identify the operation, guarantee the compiler cannot establish,
caller/callee obligation, supporting safe-code fact, failure behavior, negative
test, Miri observation and residual limitation. Read the code to check each
comment; a SAFETY comment alone is not evidence.

| Operation | Required fact | Safe wrapper fact or test | Remaining obligation |
| --- | --- | --- | --- |
| from_raw_parts in raw_sum | Non-null, initialized, live, single-allocation immutable bytes with a valid length | The wrapper borrows a Rust byte slice and caps length at 8; null empty input takes a separate branch | A different native caller must establish validity; null checks are insufficient |
| output.write in raw_sum | Aligned, live, disjoint writable u32 | The wrapper passes a distinct stack local; guarded failures preserve a sentinel | The callee must respect output bounds and not retain it |
| Calling the unsafe C-ABI function | Compatible signature, all memory preconditions, no retention/free/unwind | Fixed private function pointer, live borrows and checked status/output protocol | A foreign replacement needs a separate audit and link/build evidence |
| Reading the saved pointer in miri-dangling.rs | The allocation would need to remain live | The provided experiment frees it first and must be rejected under Miri | Never infer a native execution is safe because it happens to print 7 |

## Build and predict

Use Rust 1.97.1, edition 2024, Cargo, rustfmt and Clippy. Both roles contain a
complete lockfile and no external crates. From one role directory:

```sh
cargo fmt --all --check
rustfmt --edition 2024 --check diagnostics/*.rs
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline -- --help
cargo run --locked --offline -- --case empty
cargo run --locked --offline -- --case valid
cargo run --locked --offline -- --case cap
cargo run --locked --offline -- --case over
cargo build --locked --offline
```

The three successful cases print respectively `length=0 checksum=0`,
`length=2 checksum=24`, and `length=8 checksum=2040`, each with one final
newline, empty stderr and status 0. Over writes only `error=too-large` and a
newline to stderr, status 65. Help prints
`usage: boundary_review_lab --help | --case NAME` and a newline to stdout,
status 0. Missing, unknown, extra or non-UTF-8 arguments print that usage only
to stderr, status 64. Argument collection stops after three items. The CLI
selects four fixed fictional byte vectors and accepts no files or callbacks.
Run cargo clean, then repeat tests and build. Record streams, status, tool
versions and one independently predicted case, not just a passing summary.

## Core, continuation, choice and challenge

CORE: retain the safe baseline and define its observable contract. Audit the
supplied raw_sum before calling it. Complete CORE and LIMITS in observations.md,
including every ledger row, the need for the boundary and a safe alternative.
Add a distinct edge case that is not a copy of the supplied tests.

WORKFLOW: continue the same project. Implement a checked public checksum over
the private ABI while preserving the baseline contract. Keep raw pointers
inside the bridge; establish bounds, borrows, output lifetime and status
handling. Record exact-cap and one-over results and a clean rebuild. Explain
why checking a result after the call cannot undo an invalid callee write.

CHOICE: extend the private protocol seam with one deterministic, memory-safe
bad-status or bad-output backend. Test refusal, an unknown status, a missing
write, an impossible output and an in-range incorrect sum. State which are
detected by the wrapper and which need the independent baseline comparison.
Do not use an arbitrary caller-selected function pointer or real library.

CHALLENGE: compile unsafe-call.rs and unsafe-body.rs separately with
`rustc --edition=2024 diagnostics/NAME.rs -o NAME`; both must be refused with
E0133. explicit-call.rs and explicit-body.rs compile and print 7. Explain the
separate obligations of an unsafe function and its inner operations. Review
the supplied Miri experiment and recorded evidence below. Running Miri is
optional; never run miri-dangling.rs natively. A clean finite Miri run is not a
proof of every input, target, schedule, foreign implementation or ABI.

## Miri experiment

The CI experiment uses nightly-2026-07-16 with its Miri and rust-src components.
Toolchain and sysroot setup is separate from offline project checks. The
interpreter runs both roles' library tests, then the single supplied dangling
case in an isolated generated Cargo harness, with process timeouts. It must
accept the valid library tests and reject the freed-allocation read. No real
foreign library, network program or unbounded fuzzer is involved. The rejected
program is interpreted only under Miri; its observed value is never treated
as a valid ordinary result. Keep its source hash and actual diagnostic together.

References: [Rust Book unsafe Rust](https://doc.rust-lang.org/book/ch20-01-unsafe-rust.html),
[slice contract](https://doc.rust-lang.org/std/slice/fn.from_raw_parts.html),
[FFI and unwinding](https://doc.rust-lang.org/nomicon/ffi.html),
[Miri capabilities and limits](https://github.com/rust-lang/miri).
