# Cargo tooling reference observations

## BASELINE
Record the actual compiler and Cargo versions and host/target from the local run.
The manifest specifies edition 2024, package cargo_tooling_lab 0.1.0 and forbids
unsafe Rust in this crate. Cargo.lock version 4 lists only that package; there
are no third-party dependencies. Record actual source/lock hashes separately.

## PREDICT
Default: packet-42 followed by a newline, no program stderr, status 0. A B_c/9:
ABc9 and a newline. café-42 becomes caf-42; --- stays ---. Empty input prints
one newline. Two arguments give no stdout, the usage line on stderr and status 64.
These predictions follow the ASCII letters/digits/dash contract, not a general
claim about safe filenames or identifiers.

## CHECKS
Attach the actual format, Clippy, test and run outputs and exit statuses. The
named examples test stated cases, the ASCII test covers every code point 0–127,
and the idempotence test checks one representative mixed string. Three passed
tests do not prove every input. Cargo progress is separate from program stdout.

## CLEAN
A formatting-only error is refused by cargo fmt --all --check. cargo fmt --all
repairs formatting; repeat the refusal check and all behavioral checks. cargo
clean removes generated output; the next offline test/run rebuilds it from the
recorded source. Compare actual lockfile bytes and retain observed build output.

## COMPARE
Running an old C executable after editing its source proves behavior of that
executable only. Retain the compiler command, source hashes, flags and target,
successful build status and the resulting executable's run. Cargo manages a
build graph and selected inputs, but still requires the recorded command and
source/toolchain context to make the result reproducible.

## DIAGNOSTIC
The moved-value example is refused with E0382: ownership moves into moved and
label cannot subsequently be used. It has no runtime trace. The corrected
program borrows &label twice without moving its String and prints packet-42 on
two lines. Attach the actual compiler diagnostics and corrected run; wording and
paths can differ by compiler release.

## LIMITS
Formatting checks style, Clippy checks selected lints, tests check their cases,
and one run checks one invocation. The supplied crate has no third-party
dependencies; these commands have not refreshed an advisory database or audited
other code. For the choice activity, add a real named assertion and retain its
run rather than inferring it from this reference.
