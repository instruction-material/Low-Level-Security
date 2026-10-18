# Review states and validated transitions

Model a review workflow with three states: Draft, Reviewed and Published. Draft has no reviewer. Reviewed and Published each carry one valid reviewer name. Review is allowed only from Draft; Publish only from Reviewed. Reset returns Draft or Reviewed to Draft and removes its reviewer. Published is terminal. These rules describe this exercise's domain, not real authorization or publication infrastructure.

## Structs, enums and invariants

A struct groups fields that exist together. The starter stores two public booleans and an optional reviewer. There are eight combinations of the two flags and reviewer presence, but only three valid shapes: `0 0 -`, `1 0 Alex`, `1 1 Alex`. A published-but-unreviewed combination is invalid. So is a reviewer attached to an unreviewed draft or a reviewed state without a reviewer.

The starter checks these rules at its import and transition boundaries, but independent public fields still let other Rust code construct an invalid Session. Its raw-flags diagnostic does exactly that; `phase()` then returns an error. A passing CLI example does not prove that the representation excludes invalid states.

The reference stores a private State enum inside Session: `Draft`, `Reviewed(Reviewer)` or `Published(Reviewer)`. A value has one variant at a time, and each reviewed/published variant carries its required payload. Reviewer is a newtype whose String field is private. `Reviewer::new` validates input before creating that value. Session fields stay private; callers use constructors, queries and transitions. The reference cannot be constructed using the starter's public flag fields.

An enum does not choose correct business rules automatically. All three reference states are valid representations, but whether an event is permitted still requires the transition table. `apply` matches the current state and event, computes a complete next state, and assigns it only on success. Errors preserve the previous state. Compiler exhaustiveness checks help catch an omitted variant; they do not prove that a chosen transition is the intended one.

## Reviewer policy and legacy input

Names contain 1 through 32 Unicode scalar values, with no leading/trailing whitespace and no control characters. The single dash is reserved for absent reviewer data in the CLI. Internal spaces and non-ASCII names are valid. The starter deliberately uses a 32-byte budget, so 17 copies of é are rejected even though they are 17 scalars. Complete CHOICE by replacing that byte count with scalar counting. The reference uses `chars().count()`. Neither scalar counts nor this toy policy define grapheme counts, normalization, identity verification or user authentication.

Legacy keeps the old raw fields as input/output data. Invalid combinations remain representable there, even in the reference, because external data must be checked. `from_legacy` rejects an inconsistent flag/presence shape before validating a present name. A valid shape with an empty name produces `invalid-reviewer`; an inconsistent shape with the same empty name produces `invalid-legacy-state`. A successful `snapshot` followed by `from_legacy` preserves a valid Session. Reset must remove stale reviewer data.

## Build and observe

Open one role folder with its Cargo.toml as the working directory. Both roles are complete buildable projects with no external crates; the starter is a working flag-based baseline with the two refactor tasks explicitly unfinished. Use Rust 1.97.1 and edition 2024.

```sh
cargo fmt --all --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline
cargo run --locked --offline -- review:Bea reset review:Alex publish
cargo run --locked --offline -- --from 1 0 Alex publish
cargo run --locked --offline -- --from 0 1 -
cargo run --locked --offline -- publish
```

The no-argument example prints:

```text
start=draft reviewer=-
step=1 phase=reviewed reviewer=Alex
step=2 phase=published reviewer=Alex
```

An explicit `--from 0 0 -` with no events prints only the start line. An inconsistent legacy state prints only its error on stderr and returns 65. Publishing a Draft prints its start line, then `error=needs-review` on stderr and returns 65. Success returns 0. Unknown event syntax, malformed `--from` flags, missing arguments or non-UTF-8 arguments print usage and return 64 before applying events. All syntax is parsed first. Semantic events run in order: if a later event fails, earlier successful transitions and printed lines remain; the batch is not transactional.

For an existing Reviewed state, any Review event returns `already-reviewed` before inspecting its name. A Published state returns `already-published` for Review or Publish, and `published-cannot-reset` for Reset. Check these error priorities separately from name validation. Default output is the same in both roles; name-budget behavior and externally constructible invalid Session values distinguish the unfinished starter.

## Core, continuation, choice and challenge

CORE: enumerate the eight legacy shapes and predict all nine phase/event pairs. Refactor the public flags into a private payload enum while preserving the CLI, valid legacy round trips, error priority and unchanged-state-on-error contract. Add an independent regression with a different reviewer and event sequence.

WORKFLOW: continue the saved project. Audit legacy conversion and snapshot boundaries. Test a reviewed state without a reviewer, a draft with stale reviewer data, and an inconsistent shape containing an invalid name. Verify Reset clears its old name before re-review. Explain why raw legacy data still requires runtime validation after the internal enum refactor.

CHOICE: continue the saved project. Implement the 32-scalar policy and compare ASCII, é, crab emoji and a base letter plus combining mark. Check 32 versus 33 scalars, empty input, controls, surrounding whitespace and the reserved dash. Add independent boundary cases. Explain why a scalar is not necessarily a displayed character or a verified identity.

CHALLENGE: predict and record the three diagnostic outcomes before compiling. `non-exhaustive.rs` omits Published from a match on the real library's Phase and must receive E0004. `exhaustive.rs` handles all three variants and prints published. `raw-flags.rs` compiles against the starter and prints `error=invalid-legacy-state`, but the reference rejects its nonexistent Session fields with E0560. Compile each with the exact library built from the selected role; record stderr, stdout and status. Explain compile-time representation restrictions versus returned transition errors.

```sh
cargo build --locked --offline
rustc --edition=2024 diagnostics/non-exhaustive.rs --extern state_model_lab=target/debug/libstate_model_lab.rlib -L dependency=target/debug/deps -o non-exhaustive
rustc --edition=2024 diagnostics/exhaustive.rs --extern state_model_lab=target/debug/libstate_model_lab.rlib -L dependency=target/debug/deps -o exhaustive
./exhaustive
rustc --edition=2024 diagnostics/raw-flags.rs --extern state_model_lab=target/debug/libstate_model_lab.rlib -L dependency=target/debug/deps -o raw-flags
```

Run the last executable only when compilation succeeds. Export the complete selected role, not just main.rs. The lib.rs, manifest, lockfile, diagnostics, README and observations belong to the project. Save edits, reopen the same attempt, and continue the activities there. After `cargo clean`, rerun tests/builds and verify the lockfile and source stay unchanged by those commands. Build outputs and a green baseline suite do not complete the observation worksheet or the two intentional starter tasks.

Further reading: [Rust enums](https://doc.rust-lang.org/book/ch06-01-defining-an-enum.html) and [exhaustive matching](https://doc.rust-lang.org/book/ch06-02-match.html).
