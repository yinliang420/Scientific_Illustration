#!/usr/bin/env bash
# Run every v0.7 adversarial test. Each script runs to completion regardless
# of earlier failures so we collect every red flag in one pass.

set -u
cd "$(dirname "$0")"

PY="${HUITU_TEST_PYTHON:-/Users/ylll/miniconda3/bin/python}"
TESTS=(
  test_01_proxy_escape_hatches.py
  test_02_reload_attacks.py
  test_03_pickle_deepcopy.py
  test_04_concurrency_attacks.py
  test_05_review_module_round2.py
)

mkdir -p output

failures=0
for t in "${TESTS[@]}"; do
  echo
  echo "================================================================"
  echo "RUN $t"
  echo "================================================================"
  if "$PY" "$t"; then
    echo "[OK] $t"
  else
    rc=$?
    echo "[FAIL] $t (rc=$rc)"
    failures=$((failures + 1))
  fi
done

echo
echo "================================================================"
if [[ $failures -eq 0 ]]; then
  echo "[ALL OK] every script passed"
  exit 0
else
  echo "[$failures FAILURE(S)]"
  exit 1
fi
