#!/usr/bin/env bash
# One pass, on a machine with network access, to finish the data-source work.
#
#   1. fetch every study's input once and commit it as frozen CSV + manifest
#   2. re-run all 14 studies with the corrected core
#   3. refresh expected_output.json and report which prose now disagrees
#
# Nothing here touches git. Review, edit the prose it lists, then commit.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PY="${PYTHON:-python3}"

echo "=============================================="
echo " 0. dependencies"
echo "=============================================="
$PY -m pip install -q -U yfinance pandas-datareader akshare pandas numpy pyyaml

echo
echo "=============================================="
echo " 1. core unit tests (offline, must pass first)"
echo "=============================================="
$PY research/_core/test_core.py

echo
echo "=============================================="
echo " 2. freeze the data"
echo "=============================================="
$PY tools/freeze_data.py "$@"

echo
echo "=============================================="
echo " 3. re-run every study and diff every number"
echo "=============================================="
$PY tools/rerun_and_diff.py

echo
echo "=============================================="
echo " 4. optional: does the CRSP backend actually run?"
echo "=============================================="
echo " (skipped unless WRDS_USERNAME / WRDS_PASSWORD are set)"
$PY tools/smoke_test_wrds.py || true

echo
echo "=============================================="
echo " 5. optional: is there a fix for study 10's hole?"
echo "=============================================="
$PY tools/probe_cn_alternatives.py || true

cat <<'NOTE'

==============================================
 What to do now
==============================================
- Read rerun_report.md. It lists every number that moved and every line of
  prose that quotes an old one.
- If the movements look right, refresh the reference outputs:

      python tools/rerun_and_diff.py --accept

- Edit the prose the report names, then commit together:

      git add research/_data_frozen research/**/expected_output.json \
              research/_core tools .gitignore
      git commit -m "fix: core methodology corrections, and freeze the data they run on"

- Finally, prove the offline claim: turn the network off and run any study.
  It must complete and pass its own gate.
NOTE
