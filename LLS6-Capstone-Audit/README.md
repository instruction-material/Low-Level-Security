# LLS6 Capstone Audit

## Goals

- combine bounded copy rules and parser validation in one small program
- perform a focused audit instead of a large rewrite
- document what changed, why it changed, and how the fix was verified

## Starter Tasks

- harden packet validation before dispatch
- prevent oversized labels from corrupting state
- reject invalid mode switches cleanly
- add at least three regression cases drawn from your audit notes

## What The Solution Adds

- a fail-closed packet handler with named status values
- a checked label-copy helper that preserves null termination
- a sample audit pass that exercises success and rejection paths

## Suggested Audit Packet

- trust boundaries and assumptions
- invariants for label storage and command handling
- malformed-input list
- patch summary
- validation notes and regression cases
