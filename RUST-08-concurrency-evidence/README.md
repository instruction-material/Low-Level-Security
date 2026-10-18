# Owned work, bounded messages and joined threads

Process at most eight fictional jobs with IDs 0 through 7 and unsigned 16-bit
values. A valid run reports every supplied ID once and the sum of those values.
IDs need not be consecutive. The starter is a working sequential baseline.
The reference partitions owned jobs across exactly two workers and receives
results through a synchronous channel with capacity two. Both implement the
same public output contract; the starter does not yet demonstrate concurrency.

## Trace the pipeline

Read Job, Mode, RunError, Report, Lifecycle and validate in src/lib.rs first.
Job owns its small fields and moves into one worker partition; no job is shared
mutably. The receiving coordinator alone owns the result vector. It sorts by ID
before reporting, because arrival order is not a source-order guarantee.
At most eight items, two workers and two buffered results exist. The maximum
total is 8 × 65535 = 524280, which fits u32.

Validation checks the item limit, then each ID's range and uniqueness in input
order. Invalid input starts no workers. FailItem(id) causes that job's worker to
send a typed error and stop. The coordinator requests cooperative cancellation,
drains until disconnection and joins every started worker. Other work may have
already completed; its count is deliberately not specified on failure. There is
no partial success report. CancelBeforeStart is a deterministic cancellation
seam: both workers start, observe the flag, close their senders and are joined.
An absent failure ID behaves like a normal run.

The reference drops the coordinator's original sender before receiving. A
receiver sees disconnection only after all sender owners have dropped and all
buffered messages have been received. Waiting to join while a worker is blocked
on a full sync_channel can deadlock. The receiver is therefore drained, or
dropped on a deadline/spawn failure, before all owned handles are joined.
Builder::spawn returns a Result; a failed spawn requests cancellation and joins
the handles already obtained. A join error becomes WorkerPanicked. A fixed
worker error is tested; host thread-creation failure and arbitrary panics are
handled paths, not failures this case claims to reproduce deterministically.

AtomicBool is only a cooperative stop hint. Relaxed ordering does not publish
the result data; owned channel messages and join provide those boundaries.
Do not attach a separate data-publication claim to the flag. Cancel is not a
transaction rollback, nor a guarantee that no further work happens afterward.

## Time and termination evidence

The coordinator uses one total two-second receive deadline, not a new full
timeout per message. Workers contain only a finite partition loop and a
bounded send. Dropping the receiver releases a blocked send; each started
handle is joined. No sleep, I/O, plugin callback or unbounded producer is used.
Join has no timeout and scheduling is outside this program's control. Thus
this is a bounded-work design plus observed termination evidence, not a hard
two-second whole-process or arbitrary-callback termination guarantee. The native
verifier puts a separate 30-second process limit around the fixed probe corpus.
Retain its measured elapsed time. Never add a hanging worker to test a timeout.
The tests account for successful completion, error propagation, pre-cancellation,
sender closure and equal started/joined counts. They do not prove all schedules,
deadlock freedom for arbitrary edits, starvation freedom or production throughput.

## Build and predict

Use Rust 1.97.1, edition 2024, Cargo, rustfmt and Clippy. Both roles include a
lockfile and use no external crates. From one role directory:

```sh
cargo fmt --all --check
rustfmt --edition 2024 --check diagnostics/*.rs
cargo clippy --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
cargo run --locked --offline -- --help
cargo run --locked --offline -- --case valid
cargo run --locked --offline -- --case empty
cargo run --locked --offline -- --case cap
cargo run --locked --offline -- --case fail
cargo run --locked --offline -- --case cancel
cargo run --locked --offline -- --case duplicate
cargo run --locked --offline -- --case invalid-id
cargo run --locked --offline -- --case over
cargo build --locked --offline
```

Help prints `usage: concurrency_lab --help | --case NAME` and a newline to stdout,
status 0. Missing, extra, unknown or non-UTF-8 arguments print that same line only
to stderr, status 64. Argument collection stops after three items. The eight
named cases are fixed; the command accepts no path, URL, code or arbitrary work.

Valid prints `count=2 total=24 ids=0|3`, empty prints
`count=0 total=0 ids=-`, and cap prints
`count=8 total=524280 ids=0|1|2|3|4|5|6|7`, each with one final newline,
empty stderr and status 0. Failure cases write only stderr and status 65:
`error=worker-failed id=3`, `error=cancelled`, `error=duplicate-id`,
`error=invalid-id`, `error=too-many-items`, respectively. No output occurs until
the library run has joined its workers and returned its result.

Run `cargo clean`, then repeat tests and build. Save the whole project, including
README.md, Cargo.lock, src, diagnostics and observations.md. Record streams,
status, lifecycle and compiler version separately. A successful process exit is
not a substitute for exactly-once item accounting or started/joined equality.

## Core, continuation, choice and challenge

CORE: replace the sequential run with two owned partitions, a capacity-two
result channel, typed error propagation and a coordinator. Preserve validation,
sorted IDs and totals. Draw ownership transfers and list every sender owner.
The supplied sparse case combines nonconsecutive IDs and zero values. Add a
separate successful regression and predict its count, total and ordered IDs.

WORKFLOW: continue the same project. Predict empty, cap, failure and pre-cancel
cases. Prove each started handle is joined on success and error; explain the
drain/drop-before-join order. Add a regression and retain a clean rebuild.
Describe what the receive deadline bounds and what join does not bound.

CHOICE: study src/ledger.rs. Its single Mutex guard protects values, count and
total together; snapshots acquire the same lock. Test duplicate and invalid-ID
no-ops. The split atomic-update test forces an observer between two individually
atomic writes, without sleeping or relying on a lucky race. Explain why even
SeqCst on both counters cannot make two writes one compound transaction. Add a
snapshot invariant check and discuss poisoning without recovering invalid state.

CHALLENGE: compile the four diagnostics separately using
`rustc --edition=2024 diagnostics/NAME.rs -o NAME`.
rc-not-send and cell-not-sync must be refused with E0277; arc-owned and
scoped-shared compile and print 7. Read Rc versus Arc ownership and Send versus
Sync requirements. Arc does not make an arbitrary inner T thread-safe. Preserve
the diagnostics and explain the compiler message, then propose one valid fix.
Do not run the rejected examples or silence the check with unsafe code.

No network, real workload, daemon, shared environment mutation, arbitrary worker
callback or unbounded stress belongs in this exercise. Rust's memory safety does
not select a business invariant, ordering policy or shutdown protocol for us.

References: [Rust Book concurrency](https://doc.rust-lang.org/book/ch16-00-concurrency.html),
[bounded messages](https://doc.rust-lang.org/std/sync/mpsc/fn.sync_channel.html),
[receive timeout](https://doc.rust-lang.org/std/sync/mpsc/struct.Receiver.html#method.recv_timeout),
[joining](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html#method.join).
