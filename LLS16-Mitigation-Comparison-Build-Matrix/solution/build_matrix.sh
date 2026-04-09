#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/artifacts"
DEFAULT_BUILD="$ARTIFACT_DIR/default"
COMPARE_BUILD="$ARTIFACT_DIR/compare"

build_variant() {
	local build_dir="$1"
	local sanitizer_setting="$2"
	local extra_flags="$3"

	cmake -S "$ROOT_DIR" -B "$build_dir" \
		-DLLS_ENABLE_SANITIZERS="$sanitizer_setting" \
		-DCMAKE_CXX_FLAGS="$extra_flags" >/dev/null
	cmake --build "$build_dir" --target lls16_mitigation_matrix_solution >/dev/null
}

mkdir -p "$ARTIFACT_DIR"
build_variant "$DEFAULT_BUILD" ON "-fstack-protector-strong -D_FORTIFY_SOURCE=2"
build_variant "$COMPARE_BUILD" OFF "-fno-stack-protector -U_FORTIFY_SOURCE"

echo "=== default build ==="
"$DEFAULT_BUILD/lls16_mitigation_matrix_solution"
echo
echo "=== comparison build ==="
"$COMPARE_BUILD/lls16_mitigation_matrix_solution"

echo
echo "Record PIE, ASan, stack protector, and fortify differences in your matrix."

