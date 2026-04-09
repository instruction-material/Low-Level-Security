# LLS5 Mini Fuzzer

## Goals

- automate exploration of parser edge cases
- start from valid seeds and mutate them in controlled ways
- preserve interesting rejected cases for later regression runs

## Starter Tasks

- mutate at least one random byte in the seed packet
- occasionally perturb the length or command fields
- record how often the parser accepts versus rejects candidates
- save a few representative rejected packets for later inspection

## What The Solution Adds

- multiple mutation strategies, including byte flips and size changes
- a simple summary grouped by parser result
- a tiny "interesting cases" list to seed future regression tests

## Suggested Reflection

- Which mutation strategies found the most distinct failures?
- Why is a preserved corpus more valuable than a one-off crash?
- How do sanitizers and fuzzing complement each other?
