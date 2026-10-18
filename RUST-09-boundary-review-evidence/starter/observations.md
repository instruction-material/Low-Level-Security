# Boundary review evidence

## CORE
Record the safe contract, a distinct edge case and the named need for the boundary.
Audit every unsafe-ledger row before changing the public checksum.

## WORKFLOW
Record the wrapper's validation, pointer lifetimes, aliasing, output and status
contract. Retain exact streams/statuses and the clean rebuild.

## CHOICE
Add one deterministic memory-safe protocol seam and distinguish runtime protocol
checks from semantic equality and memory-safety obligations.

## CHALLENGE
Record both E0133 refusals and checked alternatives. Read the supplied Miri trace
or retain an actual bounded run with its compiler, source identity and limitations.

## LIMITS
Explain why comments, null checks, plausible outputs and finite dynamic tests
cannot certify arbitrary native pointers, foreign libraries or every execution.
