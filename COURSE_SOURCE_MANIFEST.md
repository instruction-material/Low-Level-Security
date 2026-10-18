# Course Source Manifest

Canonical source repository: `Low-Level-Security`

## Mapped Catalog Courses

- `rust-systems-security`: Rust Systems Security
- `low-level-security`: Low Level Security
- `low-level-security-part-2`: Low Level Security Part 2

## Verification Gate

- Run `./verify-course-source.sh` from a full checkout of this repository.
- The gate checks this manifest, the source backlog, forbidden Replit metadata,
  source-like files including Rust, and required Cargo scaffolding for all eleven
  curated Rust packs. A sparse checkout must include those packs to pass.
- Run each project's native verifier separately for format, build, test and
  runtime evidence. A presence count is not a substitute for those checks.

## Curated Rust Course Packs

RSS0–RSS10 have distinct Cargo workspaces. Each pack includes a shared reading,
starter and reference roles, lockfiles, an observations worksheet and its native
verification program. Run the pack's README commands with the declared toolchain;
the presence gate below does not compile programs or establish native behavior.

| Module | Pack | Native verifier |
| --- | --- | --- |
| RSS0 | `RUST-00-cargo-tooling-evidence` | `test/verify_rust_cargo_tooling.py` |
| RSS1 | `RUST-01-ownership-evidence` | `test/verify_rust_ownership.py` |
| RSS2 | `RUST-02-borrowing-evidence` | `test/verify_rust_borrowing.py` |
| RSS3 | `RUST-03-typed-errors-evidence` | `test/verify_rust_typed_errors.py` |
| RSS4 | `RUST-04-label-slices-evidence` | `test/verify_rust_label_slices.py` |
| RSS5 | `RUST-05-state-models-evidence` | `test/verify_rust_state_models.py` |
| RSS6 | `RUST-06-trait-pipeline-evidence` | `test/verify_rust_trait_pipeline.py` |
| RSS7 | `RUST-07-bounded-cli-evidence` | `test/verify_rust_bounded_cli.py` |
| RSS8 | `RUST-08-concurrency-evidence` | `test/verify_rust_concurrency.py` |
| RSS9 | `RUST-09-boundary-review-evidence` | `test/verify_rust_boundary.py` |
| RSS10 | `RUST-10-record-hardening-capstone` | `test/verify_rust_capstone.py` |

## Earlier Catalog Mappings

These earlier mappings remain traceable. Curated Rust packs above provide the
module-specific workspaces. Six retired offensive-lab mappings now live under
`_archived-unlinked/`, as recorded in `SOURCE_BACKLOG.md`.

| Earlier folder | Current source location |
| --- | --- |
| `LLS-01-lls1-memory-layout-and-security-tooling-supplemental-2` | `LLS-01-lls1-memory-layout-and-security-tooling-supplemental-2` |
| `LLS-01-low-level-security-lab-7` | `LLS-01-low-level-security-lab-7` |
| `LLS-02-lls1-memory-layout-and-security-tooling-supplemental-3` | `LLS-02-lls1-memory-layout-and-security-tooling-supplemental-3` |
| `LLS-02-low-level-security-lab-8` | `LLS-02-low-level-security-lab-8` |
| `LLS-03-lls2-bounds-arrays-and-safer-copy-patterns-supplemental-2` | `LLS-03-lls2-bounds-arrays-and-safer-copy-patterns-supplemental-2` |
| `LLS-03-low-level-security-lab-9` | `LLS-03-low-level-security-lab-9` |
| `LLS-04-lls2-bounds-arrays-and-safer-copy-patterns-supplemental-3` | `LLS-04-lls2-bounds-arrays-and-safer-copy-patterns-supplemental-3` |
| `LLS-04-low-level-security-lab-10` | `LLS-04-low-level-security-lab-10` |
| `LLS-05-lls3-defensive-parsers-and-binary-input-supplemental-2` | `LLS-05-lls3-defensive-parsers-and-binary-input-supplemental-2` |
| `LLS-05-low-level-security-lab-11` | `LLS-05-low-level-security-lab-11` |
| `LLS-06-lls3-defensive-parsers-and-binary-input-supplemental-3` | `LLS-06-lls3-defensive-parsers-and-binary-input-supplemental-3` |
| `LLS-06-low-level-security-lab-12` | `LLS-06-low-level-security-lab-12` |
| `LLS-07-lls4-integer-safety-state-and-defensive-data-structures-supplemental-2` | `LLS-07-lls4-integer-safety-state-and-defensive-data-structures-supplemental-2` |
| `LLS-07-low-level-security-lab-13` | `LLS-07-low-level-security-lab-13` |
| `LLS-08-lls4-integer-safety-state-and-defensive-data-structures-supplemental-3` | `LLS-08-lls4-integer-safety-state-and-defensive-data-structures-supplemental-3` |
| `LLS-08-low-level-security-lab-14` | `LLS-08-low-level-security-lab-14` |
| `LLS-09-lls5-bug-hunting-with-sanitizers-and-fuzzing-supplemental-2` | `LLS-09-lls5-bug-hunting-with-sanitizers-and-fuzzing-supplemental-2` |
| `LLS-09-low-level-security-lab-15` | `LLS-09-low-level-security-lab-15` |
| `LLS-10-lls5-bug-hunting-with-sanitizers-and-fuzzing-supplemental-3` | `LLS-10-lls5-bug-hunting-with-sanitizers-and-fuzzing-supplemental-3` |
| `LLS-10-low-level-security-lab-16` | `LLS-10-low-level-security-lab-16` |
| `LLS-11-lls6-patching-review-and-responsible-research-supplemental-2` | `LLS-11-lls6-patching-review-and-responsible-research-supplemental-2` |
| `LLS-11-low-level-security-lab-17` | `LLS-11-low-level-security-lab-17` |
| `LLS-12-lls6-patching-review-and-responsible-research-supplemental-3` | `LLS-12-lls6-patching-review-and-responsible-research-supplemental-3` |
| `LLS-13-applied-studio-7-offensive-security-lab-16-supplemental-2` | `_archived-unlinked/LLS-13-applied-studio-7-offensive-security-lab-16-supplemental-2` |
| `LLS-14-applied-studio-7-offensive-security-lab-16-supplemental-3` | `_archived-unlinked/LLS-14-applied-studio-7-offensive-security-lab-16-supplemental-3` |
| `LLS-15-applied-studio-8-offensive-security-lab-17-supplemental-2` | `_archived-unlinked/LLS-15-applied-studio-8-offensive-security-lab-17-supplemental-2` |
| `LLS-16-applied-studio-8-offensive-security-lab-17-supplemental-3` | `_archived-unlinked/LLS-16-applied-studio-8-offensive-security-lab-17-supplemental-3` |
| `LLS-23-applied-studio-12-low-level-security-lab-7-supplemental-2` | `LLS-23-applied-studio-12-low-level-security-lab-7-supplemental-2` |
| `LLS-24-applied-studio-12-low-level-security-lab-7-supplemental-3` | `LLS-24-applied-studio-12-low-level-security-lab-7-supplemental-3` |
| `LLS-25-applied-studio-13-low-level-security-lab-8-supplemental-2` | `LLS-25-applied-studio-13-low-level-security-lab-8-supplemental-2` |
| `LLS-26-applied-studio-13-low-level-security-lab-8-supplemental-3` | `LLS-26-applied-studio-13-low-level-security-lab-8-supplemental-3` |
| `LLS-27-applied-studio-14-low-level-security-lab-9-supplemental-2` | `LLS-27-applied-studio-14-low-level-security-lab-9-supplemental-2` |
| `LLS-28-applied-studio-14-low-level-security-lab-9-supplemental-3` | `LLS-28-applied-studio-14-low-level-security-lab-9-supplemental-3` |
| `LLS-29-applied-studio-15-low-level-security-lab-10-supplemental-2` | `LLS-29-applied-studio-15-low-level-security-lab-10-supplemental-2` |
| `LLS-30-applied-studio-15-low-level-security-lab-10-supplemental-3` | `LLS-30-applied-studio-15-low-level-security-lab-10-supplemental-3` |
| `LLS-31-applied-studio-16-low-level-security-lab-11-supplemental-2` | `LLS-31-applied-studio-16-low-level-security-lab-11-supplemental-2` |
| `LLS-32-applied-studio-16-low-level-security-lab-11-supplemental-3` | `LLS-32-applied-studio-16-low-level-security-lab-11-supplemental-3` |
| `LLS-33-applied-studio-17-low-level-security-lab-12-supplemental-2` | `LLS-33-applied-studio-17-low-level-security-lab-12-supplemental-2` |
| `LLS-34-applied-studio-17-low-level-security-lab-12-supplemental-3` | `LLS-34-applied-studio-17-low-level-security-lab-12-supplemental-3` |
| `LLS1-Memory-Map-Inspector` | `LLS1-Memory-Map-Inspector` |
| `LLS13-Crash-Classification-Lab` | `LLS13-Crash-Classification-Lab` |
| `LLS14-Stack-Frame-Corruption-Demo-and-Fix` | `LLS14-Stack-Frame-Corruption-Demo-and-Fix` |
| `LLS15-Heap-Lifetime-Audit` | `LLS15-Heap-Lifetime-Audit` |
| `LLS16-Mitigation-Comparison-Build-Matrix` | `LLS16-Mitigation-Comparison-Build-Matrix` |
| `LLS17-Disclosure-and-Triage-Report` | `LLS17-Disclosure-and-Triage-Report` |
| `LLS18-Exploit-Informed-Hardening-Capstone` | `LLS18-Exploit-Informed-Hardening-Capstone` |
| `LLS2-01-lls-part-2-setup-and-tooling-supplemental-2` | `LLS2-01-lls-part-2-setup-and-tooling-supplemental-2` |
| `LLS2-02-lls-part-2-setup-and-tooling-supplemental-3` | `LLS2-02-lls-part-2-setup-and-tooling-supplemental-3` |
| `LLS2-03-module-1-exploitability-triage-supplemental-2` | `LLS2-03-module-1-exploitability-triage-supplemental-2` |
| `LLS2-04-module-1-exploitability-triage-supplemental-3` | `LLS2-04-module-1-exploitability-triage-supplemental-3` |
| `LLS2-05-module-2-stack-corruption-in-toy-programs-supplemental-2` | `LLS2-05-module-2-stack-corruption-in-toy-programs-supplemental-2` |
| `LLS2-06-module-2-stack-corruption-in-toy-programs-supplemental-3` | `LLS2-06-module-2-stack-corruption-in-toy-programs-supplemental-3` |
| `LLS2-07-module-3-heap-lifetime-and-heap-metadata-concepts-supplemental-2` | `LLS2-07-module-3-heap-lifetime-and-heap-metadata-concepts-supplemental-2` |
| `LLS2-07-offensive-security-lab-16` | `_archived-unlinked/LLS2-07-offensive-security-lab-16` |
| `LLS2-08-module-3-heap-lifetime-and-heap-metadata-concepts-supplemental-3` | `LLS2-08-module-3-heap-lifetime-and-heap-metadata-concepts-supplemental-3` |
| `LLS2-08-offensive-security-lab-17` | `_archived-unlinked/LLS2-08-offensive-security-lab-17` |
| `LLS2-09-module-4-information-disclosure-and-memory-observation-supplemental-2` | `LLS2-09-module-4-information-disclosure-and-memory-observation-supplemental-2` |
| `LLS2-10-module-4-information-disclosure-and-memory-observation-supplemental-3` | `LLS2-10-module-4-information-disclosure-and-memory-observation-supplemental-3` |
| `LLS2-11-module-5-mitigation-aware-analysis-supplemental-2` | `LLS2-11-module-5-mitigation-aware-analysis-supplemental-2` |
| `LLS2-12-module-5-mitigation-aware-analysis-supplemental-3` | `LLS2-12-module-5-mitigation-aware-analysis-supplemental-3` |
| `LLS2-13-module-6-control-flow-thinking-for-defenders-supplemental-2` | `LLS2-13-module-6-control-flow-thinking-for-defenders-supplemental-2` |
| `LLS2-14-module-6-control-flow-thinking-for-defenders-supplemental-3` | `LLS2-14-module-6-control-flow-thinking-for-defenders-supplemental-3` |
| `LLS2-15-module-7-from-bug-report-to-patch-supplemental-2` | `LLS2-15-module-7-from-bug-report-to-patch-supplemental-2` |
| `LLS2-16-module-7-from-bug-report-to-patch-supplemental-3` | `LLS2-16-module-7-from-bug-report-to-patch-supplemental-3` |
| `LLS2-17-module-8-capstone-audit-supplemental-2` | `LLS2-17-module-8-capstone-audit-supplemental-2` |
| `LLS2-18-module-8-capstone-audit-supplemental-3` | `LLS2-18-module-8-capstone-audit-supplemental-3` |
| `LLS2-19-applied-studio-10-low-level-security-lab-13-supplemental-2` | `LLS2-19-applied-studio-10-low-level-security-lab-13-supplemental-2` |
| `LLS2-20-applied-studio-10-low-level-security-lab-13-supplemental-3` | `LLS2-20-applied-studio-10-low-level-security-lab-13-supplemental-3` |
| `LLS2-21-applied-studio-11-low-level-security-lab-14-supplemental-2` | `LLS2-21-applied-studio-11-low-level-security-lab-14-supplemental-2` |
| `LLS2-22-applied-studio-11-low-level-security-lab-14-supplemental-3` | `LLS2-22-applied-studio-11-low-level-security-lab-14-supplemental-3` |
| `LLS2-23-applied-studio-12-low-level-security-lab-15-supplemental-2` | `LLS2-23-applied-studio-12-low-level-security-lab-15-supplemental-2` |
| `LLS2-24-applied-studio-12-low-level-security-lab-15-supplemental-3` | `LLS2-24-applied-studio-12-low-level-security-lab-15-supplemental-3` |
| `LLS2-25-applied-studio-13-low-level-security-lab-16-supplemental-2` | `LLS2-25-applied-studio-13-low-level-security-lab-16-supplemental-2` |
| `LLS2-26-applied-studio-13-low-level-security-lab-16-supplemental-3` | `LLS2-26-applied-studio-13-low-level-security-lab-16-supplemental-3` |
| `LLS2-27-applied-studio-14-low-level-security-lab-17-supplemental-2` | `LLS2-27-applied-studio-14-low-level-security-lab-17-supplemental-2` |
| `LLS2-28-applied-studio-14-low-level-security-lab-17-supplemental-3` | `LLS2-28-applied-studio-14-low-level-security-lab-17-supplemental-3` |
| `LLS2-Bounds-Checked-Copy` | `LLS2-Bounds-Checked-Copy` |
| `LLS3-Length-Prefixed-Parser` | `LLS3-Length-Prefixed-Parser` |
| `LLS4-Ring-Buffer-Guards` | `LLS4-Ring-Buffer-Guards` |
| `LLS5-Mini-Fuzzer` | `LLS5-Mini-Fuzzer` |
| `LLS6-Capstone-Audit` | `LLS6-Capstone-Audit` |
| `RUST-01-rss0-tooling-cargo-and-why-rust-exists-supplemental-2` | `RUST-01-rss0-tooling-cargo-and-why-rust-exists-supplemental-2` |
| `RUST-02-rss0-tooling-cargo-and-why-rust-exists-supplemental-3` | `RUST-02-rss0-tooling-cargo-and-why-rust-exists-supplemental-3` |
| `RUST-03-rss1-ownership-moves-and-memory-responsibility-supplemental-2` | `RUST-03-rss1-ownership-moves-and-memory-responsibility-supplemental-2` |
| `RUST-04-rss1-ownership-moves-and-memory-responsibility-supplemental-3` | `RUST-04-rss1-ownership-moves-and-memory-responsibility-supplemental-3` |
| `RUST-04-rust-systems-lab-15` | `RUST-04-rust-systems-lab-15` |
| `RUST-05-rss2-borrowing-aliasing-and-lifetimes-supplemental-2` | `RUST-05-rss2-borrowing-aliasing-and-lifetimes-supplemental-2` |
| `RUST-05-rust-systems-lab-16` | `RUST-05-rust-systems-lab-16` |
| `RUST-06-rss2-borrowing-aliasing-and-lifetimes-supplemental-3` | `RUST-06-rss2-borrowing-aliasing-and-lifetimes-supplemental-3` |
| `RUST-06-rust-systems-lab-17` | `RUST-06-rust-systems-lab-17` |
| `RUST-07-rss3-option-result-and-typed-error-paths-supplemental-2` | `RUST-07-rss3-option-result-and-typed-error-paths-supplemental-2` |
| `RUST-08-rss3-option-result-and-typed-error-paths-supplemental-3` | `RUST-08-rss3-option-result-and-typed-error-paths-supplemental-3` |
| `RUST-09-rss4-strings-slices-collections-and-bounds-safety-supplemental-2` | `RUST-09-rss4-strings-slices-collections-and-bounds-safety-supplemental-2` |
| `RUST-10-rss4-strings-slices-collections-and-bounds-safety-supplemental-3` | `RUST-10-rss4-strings-slices-collections-and-bounds-safety-supplemental-3` |
| `RUST-11-rss5-structs-enums-and-safer-state-models-supplemental-2` | `RUST-11-rss5-structs-enums-and-safer-state-models-supplemental-2` |
| `RUST-12-rss5-structs-enums-and-safer-state-models-supplemental-3` | `RUST-12-rss5-structs-enums-and-safer-state-models-supplemental-3` |
| `RUST-13-rss6-traits-iterators-and-api-contracts-supplemental-2` | `RUST-13-rss6-traits-iterators-and-api-contracts-supplemental-2` |
| `RUST-14-rss6-traits-iterators-and-api-contracts-supplemental-3` | `RUST-14-rss6-traits-iterators-and-api-contracts-supplemental-3` |
| `RUST-15-rss7-files-parsers-and-secure-cli-design-supplemental-2` | `RUST-15-rss7-files-parsers-and-secure-cli-design-supplemental-2` |
| `RUST-16-rss7-files-parsers-and-secure-cli-design-supplemental-3` | `RUST-16-rss7-files-parsers-and-secure-cli-design-supplemental-3` |
| `RUST-17-rss8-concurrency-and-race-reduction-supplemental-2` | `RUST-17-rss8-concurrency-and-race-reduction-supplemental-2` |
| `RUST-18-rss8-concurrency-and-race-reduction-supplemental-3` | `RUST-18-rss8-concurrency-and-race-reduction-supplemental-3` |
| `RUST-19-rss9-unsafe-ffi-and-trusted-boundaries-supplemental-2` | `RUST-19-rss9-unsafe-ffi-and-trusted-boundaries-supplemental-2` |
| `RUST-20-rss9-unsafe-ffi-and-trusted-boundaries-supplemental-3` | `RUST-20-rss9-unsafe-ffi-and-trusted-boundaries-supplemental-3` |
| `RUST-21-rss10-capstone-harden-a-legacy-tool-supplemental-2` | `RUST-21-rss10-capstone-harden-a-legacy-tool-supplemental-2` |
| `RUST-22-rss10-capstone-harden-a-legacy-tool-supplemental-3` | `RUST-22-rss10-capstone-harden-a-legacy-tool-supplemental-3` |

## Source Inventory

Snapshot of tracked paths at `cdfcc58e80fc9a206c11673cfbf26f1fac95f1ea`; generated files are excluded.

- Top-level course folders: 111
- Archive containers: 1 (`_archived-unlinked/`, containing 42 retired folders)
- Verification/configuration directories: 2 (`test/` and `.github/`)
- Total tracked top-level directories: 114
- Earlier catalog mappings: 106 (100 at the top level, 6 archived)
- Curated Rust packs: 11
- Source-like files: 621, including 218 Rust files
