# Legacy record tool hardening

Preserve the supplied record format while replacing the legacy memory operations
with a bounded, owned Rust model. The runnable starter already preserves every
valid record and safely combines most malformed cases as `unclassified`. Its
unfinished work is to classify failures, justify precedence and build the final
review packet. The reference demonstrates one complete design.

## Supplied source, preserved verbatim

## Legacy Tool Hardening Capstone Case

Legacy pseudocode:

```c
int parse_record(const unsigned char *input, size_t length, Record *out) {
	unsigned char declared = input[0];
	char label[12];
	memcpy(label, input + 1, declared);
	label[declared] = '\0';
	out->kind = input[declared + 1];
	out->label = duplicate(label);
	return 0;
}
```

Valid behavior:

- record is one length byte, that many UTF-8 label bytes, and one kind byte;
- label length is 1 through 10 bytes;
- supported kinds are `1`, `2`, and `3`;
- output owns its label;
- trailing bytes are rejected.

Regression corpus:

```text
[3, 99, 97, 116, 1]
[0, 1]
[11, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 1]
[3, 99, 97]
[3, 0xFF, 0xFF, 0xFF, 1]
[3, 99, 97, 116, 9]
[3, 99, 97, 116, 1, 0]
[255]
```

Produce a behavior contract, threat model, Rust 2024 data model, bounded parser, typed errors, test matrix, dependency and lock review, and before-and-after claim table. Keep the implementation safe unless an optional supplied ABI adapter creates a genuine need for a narrow unsafe boundary. For advanced evidence, use either the supplied Miri and fuzz summaries or a fixed local run with explicit case, time, input-size, artifact, stop, and cleanup limits.

## Concrete Rust contract

`parse_record(&[u8])` returns an owned `Record` or a typed error. `Record` fields
are private; accessors expose a borrowed label and a copied kind. Label length
means UTF-8 bytes. NUL and other valid UTF-8 scalar values are permitted by this
original format; do not silently invent a printable-only rule.

Check in this order: more than 12 total bytes; empty input; zero declared length;
declared length above 10; truncated label; missing kind; trailing data; invalid
UTF-8; unsupported kind. This order makes combined faults deterministic. For
example the supplied 11-byte label record has 13 total bytes and is `too-large`;
`[11]` is `label-too-long`. `[1,255,9,0]` is `trailing-data` before encoding or
kind checks. Only the successful result allocates its owned label, at most 10
bytes. The caller already owns the input slice; this API does not bound an
allocation made by a caller before invoking it.

The reference codes are `too-large`, `empty`, `empty-label`, `label-too-long`,
`truncated-label`, `missing-kind`, `trailing-data`, `invalid-utf8`, and
`unsupported-kind`. The starter reports `too-large` for oversized input and
`unclassified` for the other malformed cases. Neither role panics on supplied
malformed input, returns a partially populated record or echoes input in errors.

## Core project: four vertical slices

1. Predict all eight original corpus results. Annotate every unchecked legacy
   read, copy, terminator write and ownership ambiguity without executing it.
   Record the valid grammar, caller trust and 12-byte accepted record bound.
2. Inspect the safe baseline. Preserve all valid behavior and its owned result.
   Introduce distinct errors and the stated precedence. Keep all fallible work
   before constructing the record. Add one focused regression per failure.
3. Test combined faults, three-byte Unicode, exact bounds and output ownership
   after mutating/dropping the source. Separate format, lint, compile, ordinary
   tests and independently generated corpus observations in the evidence table.
4. Finish `observations.md` with a threat model, before/after claim table,
   dependency/lock review, residual risks and a five-minute reproduction packet.

## Choice and challenge work

Choose one: generate valid labels for all three kinds and compare both roles;
or add a diagnostic-only formatter that escapes label bytes without changing the
parser grammar. For the challenge, mutate the fixed corpus with explicit bounds:
at most 4096 cases, each at most 13 bytes, one native process, a 30-second external
timeout, and no filesystem/network input. Record the seed/case list, counts,
stop rule and temporary-file cleanup. A deterministic bounded corpus is valid
evidence; random fuzzing and extra tool installation are optional.

This parser needs neither unsafe nor concurrency. The ledger should justify
their absence. Do not add an ABI adapter or workers merely to tick a box. If an
optional extension genuinely requires either, carry forward its separate memory
contract or work/cancellation invariant and limit claims to observed evidence.

## Reproduction

From either selected package, using Rust/Cargo 1.97.1 and Edition 2024:

```sh
cargo fmt --all --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline -- --case cat
cargo run --locked --offline -- --case unicode
cargo run --locked --offline -- --case trailing
```

The first two runs return 0 with `kind=1 label-bytes=3` and
`kind=2 label-bytes=3`, respectively. The trailing case returns 65 with empty
stdout and `error=unclassified` (starter) or `error=trailing-data` (reference) on
stderr. Every line ends with one newline. Run the last command separately when
using a shell that stops on nonzero status; the refusal is an expected result.

Use exactly `--help` or `--case NAME`. The fixed names are `cat`, `empty-label`,
`over-label`, `short`, `utf8`, `kind`, `trailing`, `declared-max`, `empty`,
`missing-kind`, `length-only`, `unicode`, `exact-max` and `combined`. Unknown,
missing, extra or non-UTF-8 arguments return 64 with the usage line only on
stderr. Help prints it on stdout and returns 0. The executable selects only
compiled fictional fixtures, does not open a supplied path and prints metadata
for valid records, never their full labels.

## Review limits and recovery

The manifest and lock select no external project crates. Record that fact and
the actual compiler, but do not turn it into a claim that the toolchain or this
program has no vulnerabilities. Tests and the fixed corpus prove selected
behavior. Safe Rust removes the demonstrated unchecked-memory path here;
grammar mistakes, resource use in a future caller, dependencies in an extension,
operational controls and future changes still need review. No whole-program
security, production activation, fuzzing or Miri run is implied.

Keep the original reading and starter separate from an edited attempt. To
reproduce a clean comparison, export or copy the selected package and retain
its Cargo files, three Rust source files and observations together.
