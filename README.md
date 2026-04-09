# Low Level Security

This repository contains the hands-on lab code for the Low Level Security
course. The course is defensive by design: students inspect toy programs,
reason about memory and input handling, fix unsafe assumptions, and prove those
fixes with tooling and regression cases.

The labs are intentionally local and classroom-scoped. They are for learning
how to harden code you control, not for building offensive payloads or
deployment workflows.

## Course Arc

### Part 1

1. `LLS1-Memory-Map-Inspector`
   Learn how stack, heap, global, static, and read-only storage differ in
   layout and lifetime.
2. `LLS2-Bounds-Checked-Copy`
   Practice safer copy rules for fixed-size buffers and explicit truncation.
3. `LLS3-Length-Prefixed-Parser`
   Build a parser that validates lengths, opcodes, and payload bytes before
   deeper logic runs.
4. `LLS4-Ring-Buffer-Guards`
   Implement a small stateful data structure that preserves invariants during
   wraparound and failure cases.
5. `LLS5-Mini-Fuzzer`
   Use structured mutation plus sanitizer-friendly builds to explore parser
   edge cases and preserve interesting failures.
6. `LLS6-Capstone-Audit`
   Harden a tiny system that combines parser validation and bounded writes, and
   document the audit trail.

### Part 2

7. `LLS13-Crash-Classification-Lab`
   Classify toy-program failures by exploitability and write short maintainer
   notes that distinguish harmless aborts from disclosure or corruption risk.
8. `LLS14-Stack-Frame-Corruption-Demo-and-Fix`
   Study how unchecked stack writes can corrupt nearby control data in a local
   toy frame model, then patch the copy rules and compare outcomes.
9. `LLS15-Heap-Lifetime-Audit`
   Review ownership and lifetime mistakes that can become use-after-free or
   double-free style security bugs, then harden object lifecycle rules.
10. `LLS16-Mitigation-Comparison-Build-Matrix`
    Compare toy builds with different mitigation settings and record how NX,
    PIE, RELRO, stack protectors, and sanitizers change the analysis story.
11. `LLS17-Disclosure-and-Triage-Report`
    Audit a disclosure-oriented toy program, patch the leak boundary, and write
    a short triage note explaining why the issue matters.
12. `LLS18-Exploit-Informed-Hardening-Capstone`
    Review a larger intentionally flawed local-only codebase, rank issues by
    impact, patch them, and deliver an audit packet plus mitigation summary.

## Repository Layout

Each lab directory contains:

- `starter/` for student-facing scaffolding and TODOs
- `solution/` for a reference implementation
- `README.md` with goals, tasks, and suggested validation steps

The starter code is intentionally incomplete but runnable. It should compile,
provide sample inputs, and make the next defensive task obvious.

## Recommended Workflow

1. Build the target with warnings and sanitizers enabled.
2. Run the starter to understand the data flow and current failure modes.
3. Implement the missing guards or state transitions.
4. Rerun the provided cases and add at least one new negative case.
5. Compare your work to the reference solution only after documenting your own
   reasoning first.

## Build

From this directory:

```bash
cmake -S . -B build
cmake --build build
```

Build a single lab if you only want one executable:

```bash
cmake --build build --target lls13_crash_classification_starter
./build/lls13_crash_classification_starter
```

On Clang and GCC, the project enables AddressSanitizer and
UndefinedBehaviorSanitizer by default. The goal is to make debugging reports
part of both course parts rather than an afterthought.

## Capstone Deliverables

The final capstone is not an exploit exercise. A good submission includes:

- a short threat model for the tiny program under review
- a list of invariants and malformed-input cases
- a narrow patch set that preserves legitimate behavior
- a regression list proving the same bug class stays fixed
- a concise audit note summarizing root cause and verification

