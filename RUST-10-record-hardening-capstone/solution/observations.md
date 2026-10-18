# Reference capstone evidence packet

This packet describes the supplied implementation and the native observations
recorded at source `5b8ed5bcb87702644e8ac277f1f0d1467fee005d`. The reference's
Rust and Cargo files are unchanged by this completed reading. An edited program
needs its own observations.

## Original contract and failure ledger

One byte declares 1 through 10 UTF-8 label bytes, followed by exactly one kind
byte in `1`, `2`, `3`. A successful result owns the complete label. Empty labels,
unsupported kinds and trailing bytes are outside the valid grammar. Label
length counts bytes; NUL and control scalars are not excluded by that grammar.
The original C pseudocode is reviewed text and was never executed.

| Original input | Reference result | Legacy diagnosis |
| --- | --- | --- |
| `[3,99,97,116,1]` | kind 1, owned `cat` | The accesses fit this particular input, but the function still lacks explicit error and allocation-ownership contracts. |
| `[0,1]` | `empty-label` | The old code accepts an empty label, violating the declared grammar even though these accesses fit. |
| `[11,97,97,97,97,97,97,97,97,97,97,97,1]` | `too-large` | This record has 13 total bytes, above the 12-byte maximum. The old code accepts an out-of-contract length; copying 11 bytes and writing index 11 happen to fit its 12-byte local array. |
| `[3,99,97]` | `truncated-label` | The three-byte copy reads beyond the supplied two label bytes; the subsequent kind read is also outside the input. |
| `[3,255,255,255,1]` | `invalid-utf8` | The accesses fit, but the old function never validates encoding. |
| `[3,99,97,116,9]` | `unsupported-kind` | The old function accepts an unsupported kind. |
| `[3,99,97,116,1,0]` | `trailing-data` | The old function ignores the final byte instead of requiring exact consumption. |
| `[255]` | `label-too-long` | The old copy reads outside input and exceeds local label capacity; the terminator and kind accesses are also out of bounds. |

Empty input adds an unchecked `input[0]` read. A declared length of 12 would
place the terminator at index 12, beyond the local array, even if the copied
bytes fit. The old `length` parameter is ignored. The shown byte-sized length
alone does not establish `size_t` arithmetic overflow on the tested platform;
the demonstrated failures are missing bounds, grammar and ownership checks.
The behavior of `duplicate`, allocation failure and responsibility for freeing
its result are unspecified by the pseudocode.

## Threat model and boundaries

The parser receives a caller-owned immutable byte slice. Its trust boundary is
the first interpretation of untrusted bytes as a record. The caller may supply
any byte values or length. The parser rejects total length above 12 before
examining a header, and checks the declared length before taking a label slice.
Successful allocation copies at most 10 label bytes. The API cannot retroactively
bound an allocation that its caller made before passing the slice.

The library has no filesystem, network, process, global state or worker effects.
The executable chooses among 14 compiled fictional fixtures and prints only
kind/length metadata or a fixed error code. It accepts no file path. The external
test harness starts bounded local compiler/test processes and removes its owned
temporary directories. Rust toolchain installation is a separate setup step;
the project checks use `--locked --offline` and no external project crates.

The compiler, standard library, allocator and host are trusted components for
this exercise. This is a local parser and CLI contract review, not a deployment
or host-hardening assessment.

## Data model and precedence

`Record` owns a `String` and a copied `Kind`; both fields are private. Safe
accessors return a borrowed label and a copied kind. Parsing performs every
fallible validation before constructing that result. UTF-8 validation precedes
the bounded `to_owned` copy. There is no partial output parameter to mutate.

The refusal order is:

1. more than 12 total bytes;
2. no header;
3. zero declared length;
4. declared length above 10;
5. fewer label bytes than declared;
6. no kind byte after a complete label;
7. trailing bytes after the kind;
8. invalid UTF-8 label;
9. unsupported kind.

The total bound avoids deeper work for oversized inputs. Structural checks then
establish complete, exact slices before content interpretation. For example,
`[11]` is `label-too-long`, while the supplied 13-byte record is `too-large`.
`[1,255,9,0]` is `trailing-data`; removing its last byte yields `invalid-utf8`
before considering kind 9. Equivalent orderings could be designed, but changing
this declared contract requires updating the callers, reading and regressions.

No unsafe block or ABI call is necessary: safe slice operations and UTF-8
validation express the full format. No concurrency is necessary: one bounded
record has no independent work requiring coordination. The unsafe and concurrency
ledgers therefore record no operations and explain those design decisions.

## Before/after claim table

| Claim | Redesign and evidence | Limit |
| --- | --- | --- |
| Avoid the demonstrated unchecked input/local-array path | Safe slices, explicit total/declared bounds and no local C buffer; malformed and exact-bound cases pass. | This does not certify the old C function or a future unsafe extension. |
| Preserve the valid format | All three kinds, byte lengths 1 through 10, NUL-containing labels and three-byte Unicode are exercised. | A finite corpus cannot enumerate every UTF-8 label. |
| Own the result | `String` field; `result_owns_label` mutates and drops the source before checking the returned `cat`. | A future borrowed API would need a different lifetime contract. |
| Keep failures distinct and deterministic | Typed variants, the eight supplied cases, combined-fault tests and independent output/status checks. | Business meaning and future grammar changes require review. |
| Bound work inside this parser | Reject more than 12 bytes before content work; at most 10 bytes copied on success. | Caller allocation, toolchain resources and global allocator exhaustion are outside this bound. |
| Avoid diagnostics that expose record contents | CLI emits fixed error codes and valid metadata; expected stderr/stdout are compared exactly. | A future label formatter must define its own escaping/privacy behavior. |
| Reproduce selected observations | Clean rebuilds, locked/offline checks and Git-free packet regression pass. | Tool output is selected evidence, not whole-program security proof. |

## Recorded native and export evidence

[Source revision](https://github.com/instruction-material/Low-Level-Security/tree/5b8ed5bcb87702644e8ac277f1f0d1467fee005d/RUST-10-record-hardening-capstone)
and [CI run](https://github.com/instruction-material/Low-Level-Security/actions/runs/39133603746)
identify the observation. The native and exported-packet checks both passed in
job `117693560785`; the independent reader matched all 16 selected committed
source/tool/workflow files against the artifacts without executing their programs.

- Native compiler: Rust 1.97.1, Edition 2024. Cargo is 1.97.1. The manifests
  declare `record_hardening_lab` 1.0.0 with no dependency section, and each lock
  contains only that local package. This is the dependency review result, not
  an advisory scan of the Rust distribution or a claim of no vulnerabilities.
- Format and warning-denying Clippy passed for both roles. Seven starter and
  thirteen reference library tests passed, then passed again after cleaning
  and rebuilding. That is 40 recorded library-test results per context.
- Fourteen named cases ran twice per role. A clean `cat` run added one per role,
  for 58 exact CLI observations. Twenty usage refusals include non-UTF-8 arguments.
- The independent corpus has 410 distinct vectors per role. It combines all
  strings of 0 through 4 bytes over `{0,1,3,255}`, valid labels over NUL/ASCII
  bytes for lengths 1 through 10 and each kind, and the supplied/additional cases.
  A local consumer exercised the public API and emitted 820 compared results.
- A plain exported packet repeated all 102 native commands without a Git
  repository or Git subprocess. The checkout run had 105 commands, including
  its three Git identity/inventory commands. Exported proofs leave checkout
  identity null and declare only the base pin and exact file hashes.
- Checkout mode refused to claim provenance in the Git-free packet. Native and
  export checkers also refused modified README bytes before running Rust, then
  restored the owned fixture. Neither refusal produced successful evidence.
- Native artifact ZIP SHA-256:
  `33caa353a09ac6793342ff3906002bb2e6ec6b23123cf5973a67f2b65e19bfb7`.
  Export artifact ZIP SHA-256:
  `28f968577cfa8dc3762adde7adf5ae469fde06dd25bf82530359f1c27aaa4dfe`.

This record uses deterministic native cases. It contains no capstone Miri run,
random-fuzz result or ABI adapter, and makes no claim that those ran.

## Five-minute reproduction packet

From the selected `solution` Cargo folder with the recorded toolchain available:

```sh
cargo fmt --all --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline -- --case cat
cargo run --locked --offline -- --case unicode
cargo run --locked --offline -- --case combined
```

The first three commands return 0; library tests report 13 passed. The two valid
runs print `kind=1 label-bytes=3` and `kind=2 label-bytes=3` on stdout and return
0. The last run returns 65, writes only `error=trailing-data` on stderr and has
empty stdout. Run that expected refusal separately in shells that stop on error.
`result_owns_label` covers mutation/drop of the input, and
`trailing_before_encoding_and_kind` covers combined-fault precedence.

An optional extension may mutate the fixed corpus under the README's explicit
4096-case, 13-byte and 30-second limits; record a new result if doing so. The
provided evidence is the fixed corpus above. Preserve the original lock and
fixture arrays for a clean comparison and retain the command output/statuses.

## Residual-risk analysis

These observations support this format and implementation at the recorded
revision. They do not prove every input, future compiler, allocator behavior,
availability, operational access control or a later extension. Even a bounded
owned-label allocation can fail if the host allocator is exhausted. Future
dependencies need their own lock/advisory review. Any future unsafe/FFI or
concurrent extension must introduce and validate its separate contract rather
than inheriting a security claim from this safe single-record parser.
