# LLS2 Bounds-Checked Copy

## Goals

- distinguish capacity from visible length
- preserve null termination for string-like buffers
- return explicit status codes instead of silently guessing

## Starter Tasks

- implement bounded copying into the fixed-size destination buffer
- preserve a valid destination state after every call
- report whether the copy succeeded, truncated, or failed validation
- review the byte dump to confirm the terminator lands where you expect

## What The Solution Adds

- a bounded copy loop using `std::min`
- printable-character validation for simple classroom inputs
- a test matrix covering short, exact-fit, empty, long, and invalid cases

## Suggested Reflection

- Why is exact-fit handling easy to get wrong?
- When is truncation acceptable, and when should an API reject input instead?
- Which return values make debugging easier later?
