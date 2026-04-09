# LLS15 Heap Lifetime Audit

Audit a small session pool for stale-handle reuse and ownership mistakes that
can turn ordinary bugs into security bugs.

## Goals

- explain stale pointer and stale handle risk in a toy allocator model
- detect where release logic fails to invalidate old references
- add lifetime checks that block reused-slot confusion

