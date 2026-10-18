# Ownership, moves and cleanup

Trace a complete Rust program through functions before changing its behavior.
This pack belongs to RSS1. It builds on the RSS0 Cargo workflow; it introduces
ownership of String, Vec and Packet values, explicit clones, and scope cleanup.

Both roles contain the same working code and diagnostics. The starter worksheet
leaves predictions and evidence open; the reference explains them.

## Files and environment

Use Rust 1.97.1 with Cargo, rustfmt and Clippy, edition 2024, on the native Linux
x86-64 validation environment. The source is safe Rust and uses only the standard
library. Cargo.lock is supplied; no crate download is needed during these checks.
Keep the root README and one complete role together. Each role has Cargo.toml,
Cargo.lock, src/main.rs, observations.md and six diagnostic source files.

After extracting a selected-role archive, enter starter or solution as applicable:

```sh
cd starter
rustc -Vv
cargo -V
cargo fmt --all --check
rustfmt --edition 2024 --check diagnostics/*.rs
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline
cargo run --locked --offline -- 'alpha'
cargo run --locked --offline -- 'alpha' empty
```

Cargo may print build messages on stderr. Distinguish them from the program's
own stderr and record exit status. To observe just the program after building:

```sh
cargo build --locked --offline
./target/debug/ownership_trace_lab
./target/debug/ownership_trace_lab alpha empty
```

If CARGO_TARGET_DIR is set, use that configured output directory instead.

## Core: an owner ledger

String and Vec own their contents. Passing them by value into make_packet
transfers that ownership; the returned Packet owns both fields. Passing a Packet
by value to relay transfers the entire value into that parameter, then returns
ownership. The old binding cannot be used as an owner after the move. A move is
a language-level ownership rule; source tracing alone does not show whether a
compiler copies, elides or rearranges machine data.

The u32 value implements Copy, so assigning copied_id leaves both integer
bindings usable. Packet does not implement Copy. Its explicit clone produces
independent String and Vec contents. Changing that clone does not change the
original. Cloning may allocate; no timing claim is part of this exercise.

Before running, fill OWNER LEDGER and PREDICT. Follow the actual names in
ownership_trace: label and bytes, packet, snapshot, moved, updated, returned.
In add_marker, follow the owned fields through destructuring, append_marker and
reconstruction. A reference such as &Packet or &str permits inspection without
taking ownership. Read borrowed_label before moving updated through relay.
Detailed borrowing restrictions and lifetime design continue in RSS2.

The default program stdout is exactly:

```text
copy=7,7
owned=packet-42 bytes=[3, 1, 4]
cloned=packet-42 bytes=[3, 1, 4]
after-edit=packet-42 bytes=[3, 1, 4, 9]
snapshot=packet-42 bytes=[3, 1, 4]
borrowed-label=packet-42
returned=packet-42 bytes=[3, 1, 4, 9]
drop=inner-second
drop=inner-first
drop=explicit
after-explicit-drop
drop=outer
```

For a changed label, replace each packet-42 with that exact text. The empty
mode changes the original/snapshot vector to [] and the updated/returned vector
to [9]. Valid runs have no program stderr and status 0. A bad vector mode, a
third argument, or a non-UTF-8 label is refused with status 64 and no stdout.
No file, network service or external target is opened by this program.

Compare actual output to predictions; mark the exact call that moves each value.
Complete CHECKS and LIMITS. The four baseline unit tests check concrete helper
behavior. They do not complete the written owner ledger.

## Continuation: scope cleanup

Continue in the same saved project. In scope_trace, predict which ScopeTag is
dropped at each closing brace and at the explicit drop call. Locals in this
ordinary block drop in reverse declaration order. drop(explicit) consumes the
tag before the following println, while outer remains until the function ends.
Complete SCOPE using the actual five-marker sequence above.

ScopeTag prints from its own Drop implementation. Those markers illustrate these
particular destructor calls. They do not measure allocations, reveal memory
addresses, log every automatic String/Vec cleanup, or prove a speed advantage.
The destructor runs before its fields are destroyed. More general temporary,
pattern and panic/unwinding rules are outside this introductory trace.

## Choice: independent owned data

Keep the saved baseline and complete CHOICE. Add one named unit test with a
new label and vector, including an empty or repeated-value case. Clone the
Packet, change the clone's label and bytes, and assert every field in both
values. Keep the baseline tests. Explain the need for a clone when two separately
editable owned values are required, compared with a borrowed read-only view.
Run formatting, Clippy and all tests again; attach the actual result and one
statement of what the added assertion would fail to catch.

## Challenge: three compile refusals and their paired fixes

Predict the result before each command. Use a disposable output directory:

```sh
ownership_lab_dir=$(mktemp -d)
rustc --edition=2024 --emit=metadata diagnostics/use-after-move.rs -o "$ownership_lab_dir/move.rmeta"
rustc --edition=2024 --emit=metadata diagnostics/use-after-drop.rs -o "$ownership_lab_dir/drop.rmeta"
rustc --edition=2024 --emit=metadata diagnostics/copy-owned.rs -o "$ownership_lab_dir/copy.rmeta"
rustc --edition=2024 diagnostics/returned-owner.rs -o "$ownership_lab_dir/returned-owner"
rustc --edition=2024 diagnostics/last-use-before-drop.rs -o "$ownership_lab_dir/last-use-before-drop"
rustc --edition=2024 diagnostics/clone-owned.rs -o "$ownership_lab_dir/clone-owned"
"$ownership_lab_dir/returned-owner"
"$ownership_lab_dir/last-use-before-drop"
"$ownership_lab_dir/clone-owned"
```

The first two commands refuse compilation with E0382; the third refuses with
E0204. They intentionally do not produce runnable programs. Diagnostic
wording and spans are observations to record, not outputs to invent. The paired
fixed programs print packet-42, packet-42, and packet-42|packet-42! respectively,
each with a final newline, empty stderr and status 0. Complete CHALLENGE: name
what was consumed, what later use was forbidden, and why each fix matches a
different desired behavior. Keep the failing examples intact.

Use an output directory owned by the current experiment and retain diagnostics
before removing that directory. Do not infer a runtime crash from a compile-time
refusal. The scope is supplied local text and values; no unsafe code or manual
memory deallocation is needed.

## Walkthrough and independent completion

First predict the owner ledger and output without the reference. Step through
each helper with an instructor or annotate it independently. Then run the exact
selected role, compare observations, and choose the independent-data test or the
compiler challenge. The reference supplies reasoning to compare afterward; it
does not replace local versions, hashes, output or an explanation of a mismatch.

Retain the edited source, observations and commands together. The core, scope
continuation, choice and challenge are four different tasks in the same workspace.

## Language references

- [Ownership, moves and clone](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)
- [References and borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html)
- [Destructor and drop-scope rules](https://doc.rust-lang.org/reference/destructors.html)
