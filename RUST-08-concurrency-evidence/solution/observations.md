# Reference design and predictions

## CORE
Two owned partitions send at most eight results through one capacity-two
channel. Only the coordinator accumulates; sorted unique IDs and u32 totals
preserve the public report. Valid predicts count=2, total=24, IDs 0|3.
The starter is sequential; replacing it is a substantive change.

## WORKFLOW
The coordinator drops its sender, drains messages or drops the receiver,
then consumes every started handle with join. Empty still starts and joins two
workers. CancelBeforeStart predicts zero received values, no report and both
handles joined. FailItem(3) predicts a typed error; the other partition may
already have finished, so no exact partial received count is promised.
Copy actual format, lint, test, clean-build, stream, status and lifecycle
evidence into an attempt; these predictions do not certify a learner's run.

## CHOICE
Ledger holds one Mutex guard across values, count and total updates and uses
the same guard for snapshots. A duplicate ID changes none of those fields.
Even SeqCst counters leave an observation point between count and total writes;
the deterministic seam demonstrates the logic error without a memory data race.
Poisoning is reported; the reference does not assume a poisoned state is valid.

## CHALLENGE
Rc is not Send; sharing a Cell reference requires Sync, which Cell lacks.
The compiler must refuse those diagnostics with E0277. Arc of an immutable
integer can move to a worker; a scoped shared integer reference outlives its
child and is Sync. Both accepted diagnostics predict stdout 7 and status 0.

## LIMITS
Cancellation is cooperative and does not undo completed work. The receive
deadline is not a timed join or OS scheduling guarantee. The native corpus is
fixed, not an exhaustive schedule proof. This project does not exercise host
spawn failure or arbitrary panics deterministically and accepts no worker I/O.
