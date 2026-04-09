# LLS17 Disclosure and Triage Report

Audit a toy serialization boundary that leaks stale internal bytes, then patch
it and write a concise triage report.

## Goals

- spot where internal memory crosses a public boundary
- explain why disclosure matters even without immediate control-flow impact
- write a short triage note with root cause, impact, and fix summary

