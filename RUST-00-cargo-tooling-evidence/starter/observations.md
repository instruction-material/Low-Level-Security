# Cargo tooling observations

## BASELINE
TODO: Record rustc -Vv, cargo -V, host/target, selected role, edition, source and
Cargo.lock hashes. Explain compiler version versus edition and the absence of
third-party dependencies in this manifest.

## PREDICT
TODO: Predict stdout, stderr and status for the default, A B_c/9, café-42, ---,
empty input and two arguments. Explain the normalization contract.

## CHECKS
TODO: Record each exact format, Clippy, test and run command with actual output
and status. Name the three tests and explain which properties they exercise.

## CLEAN
TODO: Preserve the deliberate formatting failure, repair, clean build, repeat
test/run and before/after lockfile comparison. Identify regenerated files.

## COMPARE
TODO: Explain the supplied stale C executable case and the extra evidence needed
to connect an observed run to edited source. Compare this with the Cargo record.

## DIAGNOSTIC
TODO: Predict both compilations, record actual status/stderr, explain E0382,
then record the corrected program's output and ownership behavior.

## LIMITS
TODO: State what each observed check establishes and one thing it does not.
Record the added input/test if completing the choice activity.
