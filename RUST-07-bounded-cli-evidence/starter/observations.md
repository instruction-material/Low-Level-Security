# Bounded CLI observations

## CORE
TODO: Separate decoding, record validation, domain work and display. Preserve the byte/row limits, exact outputs and ordered errors. Record the old/new boundaries and an independent regression.

## WORKFLOW
TODO: Trace arguments, checked fixture name, bounded read, UTF-8, records, report, display and exit status. Predict the exact-cap and one-over outputs, inspect both streams and repeat after cargo clean.

## CHOICE
TODO: Supply an independent short-read or failing in-memory Read implementation. Measure that acquisition consumes at most 65 bytes and keep I/O detail out of diagnostics.

## CHALLENGE
TODO: Test blank rows, CRLF, non-UTF-8, ninth-row priority, missing files, directory and symlink rejection. Separate static-fixture checks from race-free path confinement.

## LIMITS
TODO: Explain what the byte and row bounds prove, what a blocking Read can still do and why the fixture checks are not a general filesystem sandbox.
