# Typed error reference observations

## CORE
The parser returns Result<Record, ParseError>, with an Alpha kind and a u16
success value. Its failure path contains a variant, never a numeric sentinel.
The CLI alone maps a typed error to its stable public code/action and status65.
The starter's corresponding integer flags are conventions to replace.

## ERROR TABLE
MissingSeparator/add-separator precedes UnknownKind/choose-A, then
MissingValue/supply-value, InvalidNumber/use-ASCII-digits and
ValueOutOfRange/use-u16-range. B: is UnknownKind. A:65536x is InvalidNumber.
Extra colons, trailing whitespace, signs and non-ASCII digits are rejected.

## PREDICT
Default is record=Alpha value=17. A:65535 succeeds; A:65536 has no stdout,
status65 and the value-out-of-range/use-u16-range stderr line. Leading zeros
are accepted according to numeric value. Empty scan is record=absent, status0;
the scan containing A:0 is record=Alpha value=0, status0. A first B:17 rejects
even if A:17 appears later. None of these public errors repeats the input text.

## CHECKS
Record actual tool versions, commands, eight test names and clean-build
results. The u16 round-trip test covers all 65,536 valid numeric values;
separate negative tests are still needed for invalid grammar and overflow.

## LIMITS
Result makes success/failure explicit and Option represents absence. These
types do not validate external grammar automatically. Exhaustive matches catch
unhandled enum variants; a catch-all arm can hide a newly added case. The lab
does not establish application authorization or global input/resource bounds.

## ABSENCE
first_record chooses the first nonempty row. It uses Ok(None) for no candidate
and Ok(Some(record)) for a valid zero or other value. RowError retains the
zero-based index and typed cause. ok_or turns missing separator into a deliberate
error; parse_value's ? propagates that error class. map_err adds the row index,
then ? propagates RowError. A later valid row does not erase the selected error.

## CHOICE
all_records maps every nonempty row to Result<Record, RowError> and collects
the outcomes in input order. It does not use ? to return from the outer
collection on the first failure. The reference includes the typed function
and one mixed-row test; the new independent order still needs a recorded test.

## CHALLENGE
The missing-match example omits ValueOutOfRange and is refused with E0004.
Option's residual cannot propagate directly from the Result-returning example
(E0277); ok_or assigns a deliberate error before ?. A numeric sentinel is
not a Result (E0308); typed Err is the matching return contract. The paired
fixes print five error codes, Err("missing-kind"), and Err("missing-value").
Record the actual diagnostics and added regression results independently.
