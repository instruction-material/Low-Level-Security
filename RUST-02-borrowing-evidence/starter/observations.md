# Borrowing observations

## CORE
TODO: Record the owned baseline signature and the borrowed target signature.
Refactor OwnedRecord into RecordView with borrowed fields; record each removed
field copy and preserve the explicit owned_result escape. Replace the owned-field
test with a borrowed-view test while retaining the other six named tests.

## BORROW MAP
TODO: Draw each owner and referent, shared uses, exclusive uses, last uses and
the owned result. Explain which fields can survive dropping the original input
before the refactor, and why that contract changes afterward.

## PREDICT
TODO: Predict stdout, stderr and status for the default run, the documented
Unicode/empty-counter run, empty fields and a malformed record. Predict byte
length ties and explain why É does not change during ASCII normalization.

## CHECKS
TODO: Record actual versions, commands, named test results and program results,
including the clean rebuild. Compare the owned baseline and borrowed target.

## LIMITS
TODO: Explain why output equality does not prove borrowed storage, why a
lifetime annotation does not extend an owner, and what this parser rejects.

## MUTATION
TODO: Preserve a field use after normalization in a scratch diagnostic, predict
and record the compiler refusal, then repair the last-use ordering without
copying. Verify the normal and empty-field cases after the repair.

## CHOICE
TODO: Add the borrowed field selector and tests for name, role, unknown keys,
and a short-lived key. Record the relation between input and output lifetimes.

## CHALLENGE
TODO: Record predictions and actual results for all four failed compilations
and their paired fixes. Add named odd-length and wrapping-value slice tests.
Explain why the two mutable slices are disjoint.
