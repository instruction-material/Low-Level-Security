# Typed Records, Absence and Error Paths

This project implements the course's `A:17` parsing case. The starter is a
working numeric-status baseline. The reference replaces those conventions with
`Record`, `ParseError`, `Result`, `Option` and indexed `RowError` values. Both
roles define the same command-line behavior. Equal output does not establish
that an internal API expresses absence and failure in types.

## Grammar and error order

A record is exactly uppercase `A`, one colon, and one or more ASCII decimal
digits. Its numeric value is in `0..=65535`. Leading zeros are valid, including
representations longer than five digits when the numeric value still fits.
Spaces, signs, non-ASCII digits, extra colons and trailing characters are not
accepted. No trimming or normalization happens before validation.

Checks run in this order:

| Condition | Target error | Caller action |
| --- | --- | --- |
| No colon | `MissingSeparator` | `add-separator` |
| Kind is not exactly `A` | `UnknownKind` | `choose-A` |
| Value text is empty | `MissingValue` | `supply-value` |
| Any value byte is not an ASCII digit | `InvalidNumber` | `use-ASCII-digits` |
| Decimal value does not fit `u16` | `ValueOutOfRange` | `use-u16-range` |

For example, `B:` is an unknown kind before its empty value is considered.
`A:65536x` has invalid number syntax before numeric range is considered.
`A:17:2` is an invalid number. A single empty input is missing a separator.
Every malformed case returns a value to its caller; production library logic
contains no panic, `unwrap`, `expect`, process exit, file I/O or network access.

The starter uses `-1` through `-5` for those five errors and nonnegative values
for successful parsing. Its first-record API uses `usize::MAX` as an absence
marker. These are conventions that callers must remember. The target parser
returns `Result<Record, ParseError>`. A successful `Record` has kind `Alpha` and
a `u16` value. An error has a specific variant rather than a magic number.

## Absence, context and propagation

`first_record` examines the first nonempty row. Exactly empty strings are
skipped; whitespace-only strings are not. No candidate is `Ok(None)` in the
target API, which is different from `Ok(Some(record))` containing numeric zero.
An invalid first candidate returns its error even if a later row is valid.
After a valid first candidate, later rows are outside this API's selected scope.

`RowError` retains a zero-based row index and the typed parse error. The
reference converts a missing separator from `Option` with `ok_or`, converts a
parse error into row context with `map_err`, and propagates failures with `?`.
`?` does not panic or decide the caller's action. The surrounding return type
and explicit error conversion control what can propagate.

The caller-facing display names the error class without repeating the input.
The internal row index remains available to an authorized caller. Neither
`Display` nor `Debug` needs to contain the submitted record text.

The optional `all_records` API examines every nonempty row. The reference
collects successful records and indexed errors in order rather than returning
early on the first error. This deliberately differs from `first_record`.

## Build and run

Use Rust 1.97.1, Cargo, rustfmt and Clippy. Both crates declare edition 2024 and
have no third-party dependencies. From the selected role folder:

```sh
rustc -Vv
cargo -V
cargo fmt --all --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline
cargo run --locked --offline -- --record 'A:65535'
cargo run --locked --offline -- --record 'A:65536'
cargo run --locked --offline -- --scan '' 'A:0'
cargo run --locked --offline -- --scan '' ''
cargo run --locked --offline -- --scan '' 'B:17' 'A:17'
cargo clean
cargo test --locked --offline
cargo run --locked --offline
```

The default program prints `record=Alpha value=17` and a newline, with empty
stderr and status 0. The scan containing `A:0` prints `record=Alpha value=0`;
the all-empty scan prints `record=absent`. Those are distinct successful outcomes.
The out-of-range run has empty stdout, status 65 and this stderr:

```text
error=value-out-of-range action=use-u16-range
```

The scan accepts at most eight row arguments. Unsupported command shapes and
non-UTF-8 arguments use status 64 with a static message. Only the CLI selects
exit status. The parser library returns typed values without terminating a
process. These examples use bounded supplied text fixtures; the parser does
not establish application-wide input, memory, time or authorization limits.

## Core project: replace numeric status conventions

Complete CORE, ERROR TABLE, PREDICT, CHECKS and LIMITS in `observations.md`.
Refactor the starter parser into the target `RecordKind`, `Record` and five
`ParseError` variants. Remove integer failure flags from the parser API.
Keep the exact grammar, check order, range and public CLI outcomes. Give each
error one explicit caller action. Test every variant, both range boundaries,
leading zeros, extra/trailing text and fake input whose text cannot appear in
a public error. No malformed fixture can panic.

The two roles have eight named tests, including all 65,536 representable `u16`
values. Adapt API-shaped assertions when their return types change; preserve
the underlying behavior being checked. Passing the starter tests does not
complete the typed API refactor.

## Required continuation: absence and indexed failures

Continue the same saved project and complete ABSENCE. Replace the tuple absence
marker with `Result<Option<Record>, RowError>`. Keep valid zero, no candidate
and invalid candidate separate. Preserve the first nonempty row's index,
demonstrate `ok_or` and `map_err`, and explain the two `?` propagation sites.
Record why a later valid row cannot silently erase an earlier selected error.

## Choice: collect every candidate

Complete CHOICE. Refactor `all_records` into a collection of typed successes and
indexed failures. Add a named mixed-row test using a different order from the
baseline and show that rows after an error are still examined. Explain when a
caller needs all outcomes rather than the first selected candidate.

## Challenge: type boundaries and error-display regression

Complete CHALLENGE. Predict the three standalone compile refusals, run them,
and compare the paired fixes. Add new malformed cases to test grammar priority
and prove that a fake record marker never appears in public error text.

Cargo tests cover the crate sources. Compile these independent diagnostic
files separately from the selected role directory:

```sh
mkdir -p evidence
rustfmt --edition 2024 --check diagnostics/*.rs
rustc --edition=2024 --emit=metadata diagnostics/missing-match.rs -o evidence/match.rmeta
rustc --edition=2024 --emit=metadata diagnostics/option-question-mark.rs -o evidence/option.rmeta
rustc --edition=2024 --emit=metadata diagnostics/sentinel-result.rs -o evidence/sentinel.rmeta
rustc --edition=2024 diagnostics/exhaustive-match.rs -o evidence/match
./evidence/match
rustc --edition=2024 diagnostics/option-to-result.rs -o evidence/option
./evidence/option
rustc --edition=2024 diagnostics/typed-result.rs -o evidence/typed
./evidence/typed
```

The refusals are E0004 for a missing enum arm, E0277 for using an `Option`
residual directly in a `Result` function, and E0308 for returning an integer
where a `Result` is required. The fixes exhaust the match, convert absence to
a deliberate error, and return a typed `Err`. A rejected source has no runtime
result. Exhaustive types cannot by themselves prove grammar correctness.

Keep changed source, worksheet, exact commands, tool versions and actual
stdout/stderr/status results together. Compare the reference after the independent
attempt. The historical course example's process abort is a defect to remove,
not behavior to reproduce in this runnable baseline.

References: [recoverable errors](https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html),
[Result](https://doc.rust-lang.org/std/result/), [Option](https://doc.rust-lang.org/std/option/).
