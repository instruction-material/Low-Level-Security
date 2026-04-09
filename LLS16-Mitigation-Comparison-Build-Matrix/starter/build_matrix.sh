#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Build matrix starter"
echo "1. Build a default variant:"
echo "   cmake -S \"$ROOT_DIR\" -B \"$ROOT_DIR/build-lls16-default\""
echo "   cmake --build \"$ROOT_DIR/build-lls16-default\" --target lls16_mitigation_matrix_starter"
echo "2. Build a comparison variant with sanitizers off:"
echo "   cmake -S \"$ROOT_DIR\" -B \"$ROOT_DIR/build-lls16-compare\" -DLLS_ENABLE_SANITIZERS=OFF"
echo "3. TODO: inspect the resulting binaries and note which mitigations changed."

