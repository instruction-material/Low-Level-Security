# LLS16 Mitigation Comparison Build Matrix

Compare toy builds with different hardening settings and record how the
mitigation story changes.

## Goals

- verify which protections appear in a given build
- explain why mitigations help but do not replace code fixes
- build a small comparison matrix for hardened and reduced-hardening variants

## Suggested workflow

1. Build the lab with the default settings and inspect the reported features.
2. Build a comparison variant with fewer protections.
3. Record what changed in your matrix and how that changes risk analysis.

