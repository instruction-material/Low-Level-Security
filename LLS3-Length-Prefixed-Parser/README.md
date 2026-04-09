# LLS3 Length-Prefixed Parser

## Goals

- treat incoming bytes as untrusted until checks pass
- validate protocol shape before using payload data
- preserve clear rejection reasons for malformed input

## Starter Tasks

- verify the declared payload length against the actual buffer
- reject oversized payloads and unknown commands
- reject non-printable payload data
- add one more malformed packet that exercises a new failure path

## What The Solution Adds

- explicit helpers for command validation and printable checks
- status values for short buffers, mismatches, invalid commands, and bad bytes
- a reusable case runner for quick manual regression passes

## Suggested Reflection

- Which checks belong before payload decoding?
- Why should unknown commands fail closed?
- What assumptions would be hardest to debug without named status values?
