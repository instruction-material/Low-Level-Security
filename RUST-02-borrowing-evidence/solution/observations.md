# Borrowing reference observations

## CORE
The owned baseline returns an OwnedRecord containing two Strings. The target
returns RecordView<'_> containing two &str fields that point into the input.
split_once and strip_prefix return slices; the target stores those slices
directly. owned_result is a separate deliberate conversion for the final escape.
The independent-field test is replaced because returning a borrowed view cannot
promise that the view survives its input owner. The other six tests remain.

## BORROW MAP
record owns the input String. The first parsed fields are read in shared before
normalize_ascii takes an exclusive mutable reference. Their last use precedes
that mutation. The newly parsed normalized fields borrow the same input after
mutation. longer returns one of those fields. The deliberate name String is
independently owned, so printing it after drop(record) is valid.

## PREDICT
The default output is the five lines in README.md. For name=ÉA;role=ß with empty
counters, shared is ÉA|ß, normalized is name=Éa;role=ß, selected and owned-after-drop
are Éa, and halves is []. Éa is three UTF-8 bytes and ß is two. ASCII A changes;
É does not. Empty fields parse successfully and select the empty left field.
Malformed schema returns status65 with no stdout. Usage and UTF-8 refusals use64.

## CHECKS
Record the actual local tool versions, commands, seven test names, clean-build
results and outputs. These reference predictions do not replace observed results.

## LIMITS
Equal program output does not distinguish owned Strings from input-backed &str
fields. The source signatures and safe slice identity test establish the target
contract. Lifetime names express validity relationships without extending any
owner. The parser has a specific two-field schema; Rust does not validate it.
No allocation count, speedup or complete application safety is inferred.

## MUTATION
Using an input-backed field after normalize_ascii overlaps the shared borrow's
last use with the exclusive borrow and is rejected. Finishing that shared use
first permits mutation and reparsing. An owned baseline field would not express
that same borrowing relation, so compare the refactored code, not a copied field.

## CHOICE
One target signature is fn field_for<'a>(view: &RecordView<'a>, key: &str)
-> Option<&'a str>. The returned field refers to the record input. It does not
refer to either the temporary key's contents or the view struct's own storage.
The three key cases still need implementation and independently recorded tests.

## CHALLENGE
shared-and-mutable rejects overlapping shared and exclusive accesses (E0502).
two-mutable rejects overlapping ordinary mutable indexing borrows (E0499).
escaped-local rejects returning a reference to a local owner (E0515), including
with an unsupported 'static promise. missing-lifetime has two possible borrowed
inputs without an output relationship (E0106). The paired working results are
ALPHA then alpha; [2, 12]; alpha; and student. Record actual diagnostics and
the added slice tests independently. Split slices have non-overlapping ranges.
