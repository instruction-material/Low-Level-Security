# Cargo tooling evidence

Build a reproducible Rust baseline, explain what each tool checked, and save the
observations. Both roles contain the same working program; the learner task is
the evidence record in `observations.md`. The reference contains an example
record to compare after the observations have been made.

## Target and files

Use an ordinary account with Rust 1.97.1, Cargo, rustfmt and Clippy. The manifest
declares Rust 2024 edition. This package has no third-party dependencies. Record
the actual host and target from `rustc -Vv`; Rust edition and compiler version
are different facts. A newer toolchain is a separate compatibility observation.

Extract the whole downloaded project, then enter the selected `starter` or
`solution` directory, which contains `Cargo.toml`. Keep the supplied lockfile.
The two `diagnostics/*.rs` examples are separate from the Cargo build.

```sh
rustc -Vv
cargo -V
cargo fmt --all --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline
cargo run --locked --offline -- 'A B_c/9'
```

`cargo run` prints `packet-42` and a newline; the changed argument prints `ABc9`.
The program accepts zero or one UTF-8 label argument. Invalid UTF-8 produces no
stdout, writes `label must be valid UTF-8` to stderr and returns 64. More arguments produce no stdout,
write `usage: cargo_tooling_lab [label]` to stderr, and return 64. Empty input
prints only a newline. Only ASCII letters, ASCII digits and `-` survive, in their
original order. Dashes are retained individually. The program reads no files and
makes no network requests. Label normalization alone makes no promise about the
meaning or suitability of a label in another application.

The three unit tests cover named examples, every ASCII code point and idempotence.
Explain the distinction between these cases and all possible Unicode strings.
Separate Cargo's build progress on stderr from the program's stdout and record
each command's exit status.

## Required baseline

Complete BASELINE, PREDICT, CHECKS and LIMITS in `observations.md`. Predict the
default and changed outputs before running. Explain the manifest's package,
edition and lint entries; record the supplied lockfile state. Run each command
above. A zero exit from rustfmt checks formatting; Clippy checks its enabled lints;
tests check the stated cases; a run demonstrates only that invocation. None of
these is a dependency advisory database scan.

## First Cargo workflow audit

This activity continues the same project. Finish CLEAN and COMPARE. Record one
deliberate formatting error in `src/main.rs`, observe `cargo fmt --all --check`
refuse it, then run `cargo fmt --all` and repeat the check. Do not change the
program's behavior. Run `cargo clean`, repeat the offline tests and changed
argument run, and compare the lockfile bytes before and after. Explain which
generated files returned and why an existing executable alone would be weak
evidence for the edited source.

For the comparison with a manual build loop, consider this supplied case: a C
source was edited but its old executable was run without recompilation. State
what that run proves and what a compiler invocation plus its recorded inputs
would add. Cargo automates parts of this relationship; source identity, selected
features, toolchain, target and exact command still matter.

## Choice: transfer to another input

Keep the working code and change only the input. Predict and check `café-42`,
`---`, an empty argument and a chosen punctuation-heavy label. Explain ASCII
classification, character order, empty results and argument count. Add one named
unit test, rerun the same checks, and record its exact assertion and result.

## Challenge: classify a compiler diagnostic

Read both small diagnostic files. `let moved = label` transfers ownership of the
String; the later use of `label` has no value to borrow. The corrected example
passes a shared reference to `inspect`, so the caller retains ownership for both
calls. Predict whether each file compiles, then use a temporary output directory:

```sh
mkdir -p diagnostic-output
rustc --edition=2024 --emit=metadata diagnostics/moved-value.rs -o diagnostic-output/moved.rmeta
rustc --edition=2024 diagnostics/fixed-value.rs -o diagnostic-output/fixed
./diagnostic-output/fixed
```

The first compilation is expected to fail with E0382 and produce no executable.
The second succeeds and its executable prints `packet-42` twice on separate lines.
Record actual stderr and status rather than inventing a full diagnostic transcript.
Explain why the rejected program has no runtime trace. Finish DIAGNOSTIC with the
ownership change, the preserved output goal and the limit of the compiler result.

Compare the record with the reference only after making the predictions and
capturing the commands. A successful reference run does not fill in the learner's
observations or prove an unrelated project safe.
