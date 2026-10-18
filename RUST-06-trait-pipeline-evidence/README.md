# Record sources, fallible iterators and API contracts

Audit a sequence of `label=value` records. This case separates the source of
rows from the code that validates and consumes them. A trait can describe the
required behavior without requiring a particular container or privileged adapter.

## The source and consumer contract

`RowSource::rows` returns an iterator of borrowed `&str` values. The documented
source contract is a finite sequence, unchanged texts and source order. Creating
an iterator does not consume its rows. Borrowed rows remain bounded by the source
borrow; a trait method does not extend storage lifetime. The compiler checks the
method/type contract, while tests must still check ordering and chosen behavior.

`MemoryRows` owns strings. Its `pulls` counter records how many rows the iterator
actually yielded; constructing an iterator does not increment it. This is a
deterministic observation aid, not an allocator, timing or security measurement.
The reference also supplies `BorrowedRows` over an existing slice. Both sources
are local and data-only; neither requires files, network access or a registry.
These generic calls make no dynamic-object or plugin compatibility promise.

The starter is a working baseline. It declares and implements the source trait,
but its consumers accept only `MemoryRows`. `audit` eagerly copies every row
before parsing, and both consumers copy retained labels into owned strings.
The reference accepts any `RowSource`, returns borrowed labels and uses
`try_fold` so failure stops pulling at the first invalid row. Equal successful
CLI text does not prove these different API and ownership contracts.

## Record, error and ordering rules

Split on the first `=`. A missing separator is `missing-separator`. A label must
contain 1 through 16 ASCII letters, digits or dashes; otherwise use `invalid-label`.
The value must contain at least one ASCII digit and nothing else; otherwise use
`invalid-number`. Then parse an inclusive `0..=65535` value; overflow is
`value-out-of-range`. Leading zeroes are allowed. Whitespace, signs and non-ASCII
digits are not silently normalized. Label validation precedes value validation.
For example, `=no` is an invalid label, while `a=65536x` is an invalid number.

`audit` returns ordered labels, including duplicates, and their numeric total,
or the first error with a one-based source-row index. Failure returns no partial
Report. The target consumes only through that failing row; this does not roll
back observations already made by the source. Success, empty input and failure
must not reorder or change the input texts.

`all_records` has a different contract: one Result per input, in source order.
It continues after errors and retains each original one-based error index.
Collecting `Result<Vec<_>, _>` would stop at the first error; `filter_map` with
`ok()` would discard errors. Neither fulfills this all-outcomes contract. It
consumes the whole finite source. Its result container owns its entries, but
the reference's successful labels still borrow their source text.

The CLI bounds each explicit invocation to 16 rows. The library requires a
finite source but does not enforce a production input-size, execution-time or
memory policy. A trait declaration cannot prove that an arbitrary implementation
is finite or follows the documented order. The pull counter records this supplied
source's behavior; it does not make an arbitrary source free of side effects.

## Build and observe

Use Rust 1.97.1 with Cargo, rustfmt and Clippy, edition 2024. Both role folders
are complete projects with no external crates. From the selected role folder:

```sh
cargo fmt --all --check
rustfmt --edition 2024 --check diagnostics/*.rs
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline
cargo run --locked --offline -- --audit alpha=7 bad omega=17
cargo run --locked --offline -- --all alpha=7 bad omega=17
cargo build --locked --offline
```

The default example prints `count=2 total=24 labels=alpha|beta`, then `pulls=2`.
The failing audit prints `row=2 error=missing-separator` to stderr and only its
pull count to stdout: 3 in the eager starter, 2 in the lazy reference. Both return
65. All-outcomes mode prints each row's label/value or error to stdout, then
`pulls=3`; any row error gives status 65, with no error text on stderr. Otherwise
success is 0. An explicit `--audit` with no rows prints an empty report and
`pulls=0`; `--all` with no rows prints only `pulls=0`.

Malformed mode syntax, more than 16 rows or any non-UTF-8 argument produces usage
on stderr, no stdout and status 64 before rows are processed. There are no file,
network, authentication or publication operations in this example.

## Core, continuation, choice and challenge

CORE: refactor `audit` to accept a generic RowSource and return borrowed labels.
Preserve all parsing, ordering, duplicate and total rules. Replace the baseline's
owner-drop expectation with a still-live-source borrowing check and demonstrate
an independent alternate source. Record the old and new signatures, required
behavior, lifetime relationship and a custom valid/error test.

WORKFLOW: continue the same project. Remove eager row collection and compose
fallible iterator work with `try_fold`. With an invalid row in the middle, predict
then measure pulls. Prove that a later row is not requested, the first error
index stays unchanged and no partial Report escapes. Explain why earlier source
observations remain and how this differs from a transactional rollback.

CHOICE: refactor `all_records` into a generic, borrowing all-outcomes consumer.
Keep every success and error, source order and one-based indices. Add a different
deterministic in-memory source and a case with errors before and after a valid
row. Compare `Vec<Result<...>>` with `Result<Vec<...>>`; explain why dropping
errors is a different API rather than a convenient equivalent.

CHALLENGE: predict the five actual-library diagnostics before compiling them.
The missing method refuses with E0046 and mutation with a live iterator refuses
with E0502 in both roles. The alternate source receives E0308 only against the
concrete starter; it works against the generic reference. A Report used after
dropping its owner compiles in the copying starter but receives E0505 in the
borrowing reference. The scoped last-use repair compiles in both. Record actual
stdout, stderr and status separately; rejected code has no runtime result.

Compile each diagnostic with the library built from that same selected role:

```sh
rustc --edition=2024 diagnostics/missing-method.rs --extern trait_pipeline_lab=target/debug/libtrait_pipeline_lab.rlib -L dependency=target/debug/deps -o missing-method
rustc --edition=2024 diagnostics/mutate-live-iterator.rs --extern trait_pipeline_lab=target/debug/libtrait_pipeline_lab.rlib -L dependency=target/debug/deps -o mutate-live-iterator
rustc --edition=2024 diagnostics/alternate-source.rs --extern trait_pipeline_lab=target/debug/libtrait_pipeline_lab.rlib -L dependency=target/debug/deps -o alternate-source
rustc --edition=2024 diagnostics/report-after-owner-drop.rs --extern trait_pipeline_lab=target/debug/libtrait_pipeline_lab.rlib -L dependency=target/debug/deps -o report-after-owner-drop
rustc --edition=2024 diagnostics/mutation-after-last-use.rs --extern trait_pipeline_lab=target/debug/libtrait_pipeline_lab.rlib -L dependency=target/debug/deps -o mutation-after-last-use
```

Run an executable only if its compilation succeeded. The alternate source prints
`count=2 total=12`; the owned-report diagnostic prints `alpha`; the last-use repair
prints `rows=2`. Keep Cargo.toml, Cargo.lock, lib.rs, main.rs, diagnostics, this
README and observations together. After `cargo clean`, repeat tests and builds
and check source/lockfile bytes. Passing baseline tests does not complete the
generic, borrowing and laziness refactors or the written API review.

References: [traits](https://doc.rust-lang.org/book/ch10-02-traits.html),
[iterators](https://doc.rust-lang.org/book/ch13-02-iterators.html),
[Rust API Guidelines](https://rust-lang.github.io/api-guidelines/).
