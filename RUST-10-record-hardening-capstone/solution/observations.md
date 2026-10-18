# Capstone evidence packet

## Original behavior and legacy failure ledger

Record the eight original inputs, predicted outcome, memory/ownership failure,
and the evidence that supports each claim. Preserve the supplied pseudocode.

## Trust and resource boundaries

State accepted grammar, caller input ownership, byte/record limits, allowed
side effects, allocation bound and assumptions about the compiler and host.

## Redesign and error precedence

Describe private data, owned output, each refusal and combined-fault precedence.
Explain why this implementation needs neither unsafe nor worker threads.

## Before/after claims

For each claim: original path, redesign, specific test/observation, and residual
limit. Distinguish memory access, language checks, application logic and operation.

## Reproduction evidence

Record compiler/Cargo/edition, manifest and lock state, format, Clippy, test and
case outputs/statuses, dependency review and the independently generated corpus.
If adding a bounded mutation experiment, record its cases, limits, stop and cleanup.

## Five-minute review and residual risks

List commands and exact expected results. Include one combined fault, one
Unicode input and ownership after source mutation. State unproven properties.
