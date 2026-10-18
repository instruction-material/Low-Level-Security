# Ownership observations

## OWNER LEDGER
TODO: For label, bytes, packet, snapshot, moved, updated and returned, record
where ownership is introduced, transferred, borrowed, cloned and finally ends.
Distinguish the u32 copy from the String/Vec clone and struct moves.

## PREDICT
TODO: Predict stdout, program stderr and status for the default run, a changed
label, and the empty-vector run. Predict the three diagnostic refusals before
compiling them. A rejected source file has no runtime trace.

## CHECKS
TODO: Record Rust/Cargo versions, source and lock hashes, formatting, Clippy,
unit-test, default and changed run evidence. Keep Cargo's stderr separate from
program stderr and compare expected versus observed results.

## SCOPE
TODO: Predict the inner tag order, explicit drop marker, following statement and
outer marker. Capture the actual sequence. Explain why these custom markers do
not measure allocator calls or reveal physical movement of data.

## CHOICE
TODO: Add a named test using a different label and vector. Keep both the original
and clone accessible; change the clone's label and vector, then assert both
complete values. Explain which clone is needed for the stated behavior.

## CHALLENGE
TODO: For each failing diagnostic, identify the consumed or non-Copy value,
point to the later forbidden use or invalid derive, and compare the paired fix.
Explain why returning ownership, borrowing before a move, and explicit clone
solve different requirements. Do not remove diagnostics or weaken test cases.

## LIMITS
TODO: State which ownership properties are checked statically and which behavior
was observed. Name a logic or resource-exhaustion risk this lab does not prove
absent. Record any failed hypothesis and the next discriminating check.
