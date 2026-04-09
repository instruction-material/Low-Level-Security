# LLS1 Memory Map Inspector

## Goals

- identify stack, heap, global, static, and read-only storage in one process
- compare storage duration with address layout
- practice reading pointer values without treating them as magic

## Starter Tasks

- add at least one more stack object and one more heap allocation
- measure a few byte distances between nearby addresses
- write brief notes about which objects move between runs and which simply
  belong to a different storage class

## What The Solution Adds

- a small observation table for each sample object
- helper functions for consistent distance reporting
- a short interpretation section that connects addresses to lifetime

## Suggested Reflection

- Which objects sit near each other?
- Which objects are local to `main`, and which outlive it?
- Why does knowing storage duration help during security reviews?
