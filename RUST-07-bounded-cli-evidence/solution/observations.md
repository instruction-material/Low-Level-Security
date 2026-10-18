# Bounded CLI observations

## CORE
Reference: decode, parse_record/parse_records, summarize and render are separate pure stages. Preserve the byte/row limits, exact outputs and ordered errors. Record the old/new boundaries and an independent regression.

## WORKFLOW
Reference: Trace arguments, checked fixture name, bounded read, UTF-8, records, report, display and exit status. The 64-byte fixture returns count=1 total=1 labels=a; the 65-byte fixture returns only a too-large diagnostic with status 65. Predict further outputs, inspect both streams and repeat after cargo clean.

## CHOICE
Reference: Supply an independent short-read or failing in-memory Read implementation. The cursor regression measures that acquisition consumes at most 65 bytes and keep I/O detail out of diagnostics.

## CHALLENGE
Reference: Test blank rows, CRLF, non-UTF-8, ninth-row priority, missing files, directory and symlink rejection. Separate static-fixture checks from race-free path confinement.

## LIMITS
Reference: Explain what the byte and row bounds prove, what a blocking Read can still do and why the fixture checks are not a general filesystem sandbox.
