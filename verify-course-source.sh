#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$root"

fail() {
  printf 'course source verification failed: %s\n' "$1" >&2
  exit 1
}

require_file() {
  [ -f "$1" ] || fail "missing $1"
}

require_file "COURSE_SOURCE_MANIFEST.md"
require_file "SOURCE_BACKLOG.md"

rust_packs=(
  "RUST-00-cargo-tooling-evidence"
  "RUST-01-ownership-evidence"
  "RUST-02-borrowing-evidence"
  "RUST-03-typed-errors-evidence"
  "RUST-04-label-slices-evidence"
  "RUST-05-state-models-evidence"
  "RUST-06-trait-pipeline-evidence"
  "RUST-07-bounded-cli-evidence"
  "RUST-08-concurrency-evidence"
  "RUST-09-boundary-review-evidence"
  "RUST-10-record-hardening-capstone"
)

for pack in "${rust_packs[@]}"; do
  require_file "$pack/README.md"
  for role in starter solution; do
    for required in Cargo.toml Cargo.lock observations.md src/main.rs; do
      require_file "$pack/$role/$required"
    done
  done
done

if find . \
  \( -path './.git' -o -path './node_modules' -o -path './Library' -o -path './Temp' -o -path './Logs' \) -prune -o \
  \( -name '.replit' -o -name 'replit.nix' -o -name 'replit.nix.backup' -o -name 'replit_zip_error_log.txt' \) -print -quit | grep -q .; then
  fail "replit metadata should not be committed"
fi

source_count="$(find . \
  \( -path './.git' -o -path './node_modules' -o -path './Library' -o -path './Temp' -o -path './Logs' \) -prune -o \
  -type f \( -name '*.rs' -o -name '*.py' -o -name '*.java' -o -name '*.cpp' -o -name '*.c' -o -name '*.h' -o -name '*.hpp' -o -name '*.js' -o -name '*.ts' -o -name '*.swift' -o -name '*.cs' -o -name '*.md' \) -print | wc -l | tr -d ' ')"

[ "$source_count" -gt 0 ] || fail "no source-like files found"

printf 'course source verification passed: %s source-like files\n' "$source_count"
