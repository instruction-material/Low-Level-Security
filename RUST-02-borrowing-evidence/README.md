# Borrowed Records and Lifetimes

This project converts an owned record parser into a borrowed view. The input
`String` owns the text. A `RecordView<'a>` should contain two `&'a str` fields
that refer into that input, rather than two separately owned `String` fields.

The starter is a working owned baseline. Its `OwnedRecord` intentionally copies
the parsed fields with `to_owned`. The reference implements the borrowed target.
Both produce the same text output; output equality alone cannot establish which
ownership contract an implementation has.

## Record and borrowing contracts

The exact schema is `name=<text>;role=<text>`, in that order, with exactly one
semicolon. Empty fields, spaces, Unicode and `=` inside either value are allowed.
Keys are lowercase and case-sensitive. The parser returns an error for a missing
separator, a different key or an extra field. It returns field values unchanged.

`split_once` and `strip_prefix` return string slices. In the borrowed version,
the input's lifetime bounds both returned fields. The `'_` in the return type
uses the single input reference's elided lifetime. It does not create storage or
extend the input owner. A named lifetime would express the same relationship.

`normalize_ascii(&mut str)` changes ASCII uppercase bytes to lowercase in the
existing input. It leaves other UTF-8 characters unchanged, including `É` and
`ß`, and preserves byte length. It is not Unicode case folding. A shared field
view must have its last use before this exclusive mutation starts. The reference
prints the first view before mutation, then parses a new view afterward.

`longer<'a>(&'a str, &'a str) -> &'a str` returns the longer input by byte length,
choosing the left input on a tie. Both inputs must remain valid for the chosen
common lifetime at the call. The annotation describes a relationship; it cannot
make a local `String` live longer or promise the returned reference is `'static`.

`bump_halves(&mut [u8])` splits at `len / 2`. The left slice adds 1 to each byte;
the right adds 10, using `wrapping_add`. The slices are disjoint. Empty input is
valid, and an odd input places the extra byte in the right slice. Writing through
disjoint slices is different from keeping two ordinary indexing borrows alive.

`owned_result(&str) -> String` deliberately copies one final name. That result
can outlive the input owner. Keep this explicit owned result when ownership must
escape; do not change borrowed parser fields into owned copies to hide the
borrowing requirement. The code does not measure allocations or pointer speed.

## Build and run

Use a native Rust 1.97.1 toolchain with rustfmt and Clippy. The crates use edition
2024 and have no third-party dependencies. From the selected role folder:

```sh
rustc -Vv
cargo -V
cargo fmt --all --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline
cargo run --locked --offline -- 'name=ÉA;role=ß' empty
cargo clean
cargo test --locked --offline
cargo run --locked --offline
```

The default run prints:

```text
shared=ALPHA|ADMIN
normalized=name=alpha;role=admin
selected=alpha
halves=[2, 3, 13, 14]
owned-after-drop=alpha
```

Predict the Unicode and empty-counter run before trying it. Compare UTF-8 byte
lengths when choosing `selected`. Program success is status 0 with empty stderr.
Invalid arguments or non-UTF-8 record arguments use status 64. Invalid record
syntax uses status 65. Both refusals have empty stdout and a specific stderr
message. An empty name and role are valid data, not a syntax refusal.

The Cargo checks cover `src/main.rs`. The independent diagnostic files are
compiled separately. From the same selected role directory:

```sh
mkdir -p evidence
rustfmt --edition 2024 --check diagnostics/*.rs
rustc --edition=2024 --emit=metadata diagnostics/shared-and-mutable.rs -o evidence/shared.rmeta
rustc --edition=2024 --emit=metadata diagnostics/two-mutable.rs -o evidence/two.rmeta
rustc --edition=2024 --emit=metadata diagnostics/escaped-local.rs -o evidence/local.rmeta
rustc --edition=2024 --emit=metadata diagnostics/missing-lifetime.rs -o evidence/lifetime.rmeta
rustc --edition=2024 diagnostics/last-use-before-mutation.rs -o evidence/last-use
./evidence/last-use
rustc --edition=2024 diagnostics/split-borrows.rs -o evidence/split
./evidence/split
rustc --edition=2024 diagnostics/owned-result.rs -o evidence/owned
./evidence/owned
rustc --edition=2024 diagnostics/related-lifetimes.rs -o evidence/related
./evidence/related
```

The first four compilations intentionally fail, respectively with E0502, E0499,
E0515 and E0106. A rejected source file has no runtime result. Each subsequent
working file demonstrates a specific repair: last use before mutation, disjoint
slices, an owned return value or a valid relationship between input lifetimes.
Neither adding `'static` nor adding a lifetime name allocates or preserves a
local owner's data.

## Core project: borrowed record refactor

Complete CORE, BORROW MAP, PREDICT, CHECKS and LIMITS in `observations.md`.
Replace the starter's `OwnedRecord` with `RecordView<'a>`, use borrowed fields,
and update the parser return type. Remove the two field copies without using
unsafe code, leaks, global storage, `'static` or a cloned input buffer. Preserve
all valid and invalid input behavior and the deliberate `owned_result` contract.

The starter's ownership test establishes its initial independent-field contract.
After refactoring, replace that particular test with a borrowed-view test tied
to a still-live input, while retaining the other six tests. Explain why a test
that reads fields after dropping the input is no longer a valid target behavior.
The reference includes one safe pointer-equality check for the exact field
slices; an address value by itself does not prove a general lifetime contract.

## Required continuation: last use and exclusive mutation

Continue the same saved project and complete MUTATION. Draw the input owner,
both shared field views, their last uses and the later mutable borrow. Move a
field use after normalization in a scratch diagnostic, predict the refusal,
then repair the ordering without copying the fields. Record the compiler's
actual explanation and both standard and empty-field run results.

## Choice: independent selector input

Complete CHOICE. Add a borrowed field selector that returns a field from a
`RecordView` based on a separate `&str` key. Tie the return lifetime to the view's
input data, not to the temporary key string. Support `name`, `role` and an
unknown key, and add tests with a short-lived key and a longer-lived record.
Do not return a newly owned field or keep the key alive unnecessarily.

## Challenge: four compiler boundaries

Complete CHALLENGE. Predict each intentional diagnostic before compiling it.
For each, identify the conflicting accesses or unavailable owner and explain
why its paired fix preserves the intended behavior. Add an odd-length and a
wrapping-value slice test, then compare ordinary indexing with `split_at_mut`.
Do not treat a compiler refusal as a process trace or a performance measurement.

## Completion evidence

Keep the changed source, worksheet, exact commands, actual tool versions, test
names, outputs and statuses together. Passing baseline checks does not complete
the parser refactor, new selector or written reasoning. Compare the reference
only after recording the independent attempt. The Rust borrow rules support
memory safety in this safe code; they do not validate the record schema or its
business meaning automatically.

References: [borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html),
[lifetimes](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html),
[split_at_mut](https://doc.rust-lang.org/std/primitive.slice.html#method.split_at_mut),
[split_once](https://doc.rust-lang.org/std/primitive.str.html#method.split_once).
