# Typed error observations

## CORE
TODO: Refactor the numeric-status parser into RecordKind, Record and ParseError.
Record the old and new signatures and adapt type-shaped assertions while
preserving all grammar, range, display and CLI behavior.

## ERROR TABLE
TODO: Map each malformed class to its typed variant, public code, caller action
and one independent test. Explain precedence for B: and A:65536x.

## PREDICT
TODO: Predict default, maximum, one-over, leading-zero, trailing-text, empty
scan, valid-zero scan and first-invalid scan stdout, stderr and exit status.

## CHECKS
TODO: Record actual versions, all checks and eight test names before and after
a clean rebuild. Keep the new malformed-input cases with their results.

## LIMITS
TODO: Explain what Result, Option and exhaustive matches enforce, what the
grammar still has to validate, and what input/resource policies remain outside
this fixture parser. Distinguish a compiler refusal from a runtime outcome.

## ABSENCE
TODO: Refactor first_record into Result<Option<Record>, RowError>. Preserve
the index and distinguish valid zero, no row and rejected row. Explain ok_or,
map_err and both question-mark propagation sites.

## CHOICE
TODO: Refactor all_records into typed successes and indexed failures. Add a
different mixed-row test and verify that an error does not stop later rows.

## CHALLENGE
TODO: Predict and preserve all three compiler refusals and working fixes.
Add new grammar-priority and fake-marker error-display regression cases.
