# Packet Labels, Byte Ranges and Unicode Slices

The original course case turns `packet-42!` into `packet-42` by retaining only
ASCII letters, ASCII digits and dashes. The starter deliberately retains its
unfinished identity filter. Complete that filter before treating its label
output as correct. The reference performs the original filtering task.

The added range APIs make the module's strings, collections and bounds work
concrete. The starter returns owned copies from checked ranges. The reference
returns borrowed views. Both roles have the same range outcomes; equal printed
text does not establish that an API avoids copying its selected data.

## Index units and range contracts

`String` owns UTF-8 bytes. `&str` borrows valid UTF-8 text; `&[u8]` borrows bytes.
`Vec<char>` owns Unicode scalar values. Every range is half-open: start is
included and end is excluded. A byte offset, scalar position and displayed
grapheme are different units. The combining sequence `e\u{301}` contains two
scalars even when displayed as one accented letter. This project does not
implement grapheme segmentation.

| Function | Index unit | Starter result | Target result |
| --- | --- | --- | --- |
| `sanitize` | Characters examined against the ASCII allowlist | Unfinished identity `String` | Filtered `String` |
| `str_window` | UTF-8 byte offsets | `Result<String, WindowError>` | `Result<&str, WindowError>` |
| `byte_window` | Byte offsets | `Result<Vec<u8>, WindowError>` | `Result<&[u8], WindowError>` |
| `char_window` | Unicode scalar positions | Collected `Result<String, WindowError>` | Borrowed `Result<&str, WindowError>` |

Check reversed ranges first. Next reject an end beyond the relevant length.
String byte ranges must also start and end on UTF-8 character boundaries.
`a🦀bc` has seven bytes and four scalars: its crab occupies bytes `1..5`.
The byte range `2..3` is a valid one-byte byte slice, but cannot form `&str`.
The scalar range `1..2` selects the complete crab. An empty string range is
valid only at a character boundary; byte and scalar empty ranges use their
own lengths. Preserve `Reversed`, `OutOfBounds` and `NotCharBoundary` rather
than converting every failure into an empty successful slice.

## Build and observe

Use Rust 1.97.1 with Cargo, rustfmt and Clippy. The crates use edition 2024 and
no third-party packages. From the selected role directory:

```sh
rustc -Vv
cargo -V
cargo fmt --all --check
rustfmt --edition 2024 --check diagnostics/*.rs
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline
cargo run --locked --offline -- --sanitize 'packet-42!'
cargo run --locked --offline -- --window 'a🦀bc' 1 5
cargo run --locked --offline -- --bytes 'a🦀bc' 2 3
cargo run --locked --offline -- --chars 'a🦀bc' 1 2
cargo run --locked --offline -- --window 'a🦀bc' 2 3
cargo clean
cargo test --locked --offline
cargo run --locked --offline
```

The unfinished starter default is `label=packet-42!`; the completed target is
`label=packet-42`. Both range examples print `window=🦀 bytes=4 scalars=1`, and
the byte example prints `bytes=[159]`. The non-boundary string range has empty
stdout, status 65 and stderr `error=not-character-boundary`. Reversed and
out-of-bounds errors use their own codes. Invalid command shapes, index syntax
or non-UTF-8 arguments use status 64. Successful results use status 0. The
library returns values; only the CLI selects an exit status.

## Core: complete the existing label filter

Complete CORE, LABEL CASES, PREDICT, CHECKS and LIMITS in `observations.md`.
Implement the original ASCII allowlist. Preserve allowed text and empty input;
reject punctuation, underscores, whitespace, controls and non-ASCII letters by
removing them. Replace the deliberately named identity-baseline test with new
filter assertions. Check a custom mixed Unicode case and all ASCII values.
Allowed-character filtering does not establish context-specific HTML, SQL or
shell escaping, nor an application-wide size or resource policy.

## Required continuation: checked borrowed ranges

Continue the same saved project and complete WINDOWS. Refactor `str_window`
and `byte_window` to return views tied to their input. Preserve error priority,
zero-length behavior and every range outcome. Add a new multibyte fixture and
an explicit source-offset diagram. Explain why bytes inside a scalar can form
`&[u8]` while the same interval cannot form `&str`. Adapt return-type-shaped
tests while preserving the behavioral checks.

## Choice: map scalar positions to byte boundaries

Complete CHOICE. Replace the temporary `Vec<char>` in `char_window` with a
borrowed result using `char_indices`. Handle the end-of-string boundary and
empty ranges. Add a combining-mark fixture and explain why scalar slicing
still does not implement grapheme slicing. Compare the borrowed result's
source range with the owned baseline rather than inferring timing results.

## Challenge: distinguish compilation, panic and returned error

Complete CHALLENGE. Compile the standalone files separately from Cargo tests.
`string-index.rs` intentionally fails with E0277. The three direct range/index
examples compile but panic with status 101. Each paired checked example runs
successfully and reports `Some` or `None` instead. Predict each result first.

```sh
mkdir -p evidence
rustc --edition=2024 --emit=metadata diagnostics/string-index.rs -o evidence/index.rmeta
rustc --edition=2024 diagnostics/byte-out-of-bounds.rs -o evidence/bytes
./evidence/bytes
rustc --edition=2024 diagnostics/non-boundary-slice.rs -o evidence/text
./evidence/text
rustc --edition=2024 diagnostics/reversed-range.rs -o evidence/range
./evidence/range
rustc --edition=2024 diagnostics/scalar-index.rs -o evidence/scalar
./evidence/scalar
rustc --edition=2024 diagnostics/checked-byte.rs -o evidence/checked-byte
./evidence/checked-byte
rustc --edition=2024 diagnostics/checked-string.rs -o evidence/checked-string
./evidence/checked-string
rustc --edition=2024 diagnostics/checked-range.rs -o evidence/checked-range
./evidence/checked-range
```

A safe Rust bounds panic stops this process; it is not an out-of-bounds memory
read. A compile refusal has no runtime output. The project library's checked
functions return errors rather than reproducing those diagnostic panics.
Retain source, worksheet, exact commands, tool versions and actual stdout,
stderr and status together. Compare the reference after the independent attempt.

References: [Rust strings](https://doc.rust-lang.org/book/ch08-02-strings.html),
[`str::get`](https://doc.rust-lang.org/std/primitive.str.html#method.get),
[`slice::get`](https://doc.rust-lang.org/std/primitive.slice.html#method.get).
