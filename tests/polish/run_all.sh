#!/usr/bin/env bash
# Stand-alone driver for the v0.6 polish test suite.
#
# Usage:
#   bash tests/polish/run_all.sh
#
# Each test prints `[PASS] case_NN <desc>` or `[FAIL] ... — reason`.
# Exit code 0 if every case passed, 1 otherwise.

set -uo pipefail

# Resolve repo root from the script's location, not CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PYTHON="${PYTHON:-/Users/ylll/miniconda3/bin/python}"
if ! command -v "${PYTHON}" >/dev/null 2>&1; then
    PYTHON="python"
fi

cd "${REPO_ROOT}"

# Run pytest, surface [PASS]/[FAIL] lines, then a summary.
"${PYTHON}" -m pytest tests/polish/ -v --tb=short --no-header -s 2>&1 \
    | tee /tmp/huitu_polish_run.log

echo
echo "================== POLISH SUITE SUMMARY =================="
n_pass=$(grep -cE "\[PASS\]" /tmp/huitu_polish_run.log || echo 0)
n_fail=$(grep -cE "\[FAIL\]" /tmp/huitu_polish_run.log || echo 0)
echo "[PASS] cases: ${n_pass}"
echo "[FAIL] cases: ${n_fail}"
echo
echo "================== FAILED CASES =========================="
grep -oE "\[FAIL\][^$]*" /tmp/huitu_polish_run.log | sort -u || echo "(no failed cases)"

# Exit code from pytest itself
exit "${PIPESTATUS[0]}"
