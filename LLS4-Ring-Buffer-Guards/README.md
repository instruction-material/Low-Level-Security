# LLS4 Ring Buffer Guards

## Goals

- model a low-level structure with explicit invariants
- preserve internal state on failure
- reason about wraparound without losing track of head, tail, and count

## Starter Tasks

- reject writes that do not fit in the remaining capacity
- reject reads larger than the stored byte count
- stage state changes so failures leave the buffer unchanged
- verify behavior with exact fills, wraparound reads, and impossible requests

## What The Solution Adds

- staged index updates before committing state
- invariant checks and debug snapshots for logical buffer contents
- a sample run that hits success, wraparound, and over-request cases

## Suggested Reflection

- Which values must stay in sync for the object to remain trustworthy?
- Why is "unchanged on failure" such a useful security property?
- How would you explain the ring buffer invariants in a code review?
