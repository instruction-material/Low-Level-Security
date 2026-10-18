# A bounded fixture CLI and pure record parser

Read one supplied fixture, validate every record and print a single report.
The starter already runs and follows the observable contract. Its process
function mixes decoding, record validation, accumulation and display. Refactor
those stages into independently testable functions. The reference demonstrates
one decomposition, not an additional feature specification.

## Argument and fixture contract

Use exactly `--help` or `--file NAME.txt`. Help writes the usage line to stdout
and returns 0. Missing, extra, unknown or non-UTF-8 arguments write that line to
stderr, with empty stdout and status 64. Argument collection stops after three
items, enough to reject every overlong invocation of this two-item grammar.

A fixture name has a nonempty ASCII letter/digit/dash/underscore stem, the exact
suffix `.txt` and at most 32 bytes overall. Paths, drive prefixes, dots in the
stem and separators are rejected before a read. The fixture directory is the
selected Cargo package's supplied `fixtures` folder, located from the package
manifest when compiled. Changing the working directory does not redirect it.
Do not overwrite the original fixtures while doing an exercise.

The checked entry must be a regular file. A missing fixture reports
`error=read kind=not-found`; a directory or symbolic-link entry reports
`error=read kind=not-regular`. Both have status 66. Other I/O errors report
`error=read kind=io` with status 74. Each diagnostic ends with one newline and
uses stderr only; it does not include input text, a supplied path or an OS error.

This is a fixed, reviewed fixture exercise. `symlink_metadata` checks the entry
it observes; a later open is a separate operation. The code does not provide
race-free confinement against a concurrent filesystem writer, check every parent
component or replace OS access policy. Do not turn this case into a general file
browser or use a real secret-bearing directory. The directory must stay unchanged
while the command runs; all supplied and verifier-created inputs are fictional.

## Bounded acquisition and parsing

`acquire<R: Read>` accepts a file or an in-memory reader. `Read::take(65)` allows
at most 65 returned bytes. One byte beyond the 64-byte input limit is necessary
to distinguish an exact-limit input from an oversized one. Read errors produce
no input value. Short reads are not necessarily EOF, so the adapter is read until
EOF, the limit or an error. A byte bound does not impose a time bound on an
arbitrary blocking reader, nor does it specify exact allocator overhead.

The input byte limit is checked before decoding. Reject malformed UTF-8 before
examining records. These errors use status 65 and respectively report
`error=input kind=too-large limit=64` and `error=input kind=invalid-utf8`.
The pure process function checks the same bound even if called without a file.

Input contains zero through eight `label=value` records, separated by LF. One
final LF is optional. Empty input is valid; a blank record is not. CRLF is not
normalized. Before parsing a ninth record, report
`error=input kind=too-many-rows limit=8`, status 65. Within each earlier record,
split at the first `=`. Then check, in order:

- A separator exists, otherwise `missing-separator`.
- Label: 1 through 16 ASCII letters, digits or dashes, otherwise `invalid-label`.
- Value: one or more ASCII digits only, otherwise `invalid-number`.
- Number: inclusive 0 through 65535, otherwise `value-out-of-range`.

A record error reports `error=record line=N kind=KIND`, with a one-based line
number, a newline, empty stdout and status 65. The first error wins. Whitespace,
signs, extra separators and Unicode digits are not silently repaired. Leading
zeroes are valid. For example `=no` fails the label check, while `a=65536x` fails
the digit check before numeric range is considered.

Success preserves source order and duplicate labels. It writes exactly
`count=N total=T labels=LABELS` and a newline to stdout, nothing to stderr and
returns 0. Labels are joined with `|`; an empty report uses `labels=-`.
The supplied valid fixture prints `count=2 total=24 labels=alpha|beta`.
The 64-byte fixture prints `count=1 total=1 labels=a`. The 65-byte fixture is
rejected. No report is printed until every record succeeds; this does not imply
that reads or earlier external effects can be rolled back.

## Build and trace

Use Rust 1.97.1, edition 2024, with Cargo, rustfmt and Clippy. Each role is a
complete project with a lockfile and no external crates. From that role folder:

```sh
cargo fmt --all --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline -- --help
cargo run --locked --offline -- --file valid.txt
cargo run --locked --offline -- --file empty.txt
cargo run --locked --offline -- --file malformed.txt
cargo run --locked --offline -- --file cap.txt
cargo run --locked --offline -- --file over.txt
cargo build --locked --offline
```

Record stdout, stderr and status separately. Running the built executable from
another working directory must select the same package fixtures. `cargo clean`
removes build outputs; repeat the tests and build afterward. Preserve Cargo.toml,
Cargo.lock, src, fixtures, observations.md and this README together.

## Core, continuation, choice and challenge

CORE: refactor the monolithic process function into decoding, record parsing,
domain work and display. Keep the supplied argument, read and diagnostic
contracts. Use the reference's stage boundaries only after making an attempt.
Add a new regression, record the old/new boundaries and explain why a pure
parser neither opens a file nor writes a report. The reference borrows record
labels from decoded input; keep that storage alive while records are used.

WORKFLOW: continue the same project and trace argument handling, fixture-name
validation, acquisition, UTF-8, record validation, reporting and exit status.
Predict exact-cap, over-cap, malformed and missing-file outcomes, then run them.
Show a valid first row followed by a failure with no partial stdout. Record an
independent source-order case, both streams, status and the clean rebuild.

CHOICE: supply a different deterministic short-read or failing `Read` test double.
Check that a short read does not end acquisition prematurely, an oversized cursor
advances only 65 bytes and private I/O details are absent from diagnostics. Extend
the bounded corpus with a fixed number of fictional byte cases and record the
budget. Keep the library's byte limit separate from a blocking reader's time.

CHALLENGE: predict blank-row, CRLF, malformed UTF-8, ninth-row, directory and
symbolic-link behavior. Use only copied fixtures or in-memory sources. Explain
why metadata followed by open is not an atomic path-confinement primitive,
identify an assumption the exercise needs and add a regression for a separate
error-priority boundary. No recursion, network, child command, unreviewed link,
input overwrite or unbounded fuzzing belongs in this exercise.

References: [Read and take](https://doc.rust-lang.org/std/io/trait.Read.html#method.take),
[symlink_metadata](https://doc.rust-lang.org/std/fs/fn.symlink_metadata.html),
[CLI exit status](https://rust-cli.github.io/book/in-depth/exit-code.html).
