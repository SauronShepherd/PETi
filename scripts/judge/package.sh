#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python "$repo/scripts/judge/check_doc_drift.py"
python "$repo/scripts/judge/generate_judge_docs.py" --repo "$repo"
python "$repo/scripts/judge/scan_secrets.py"
echo "Judge source package checks passed; external runtime evidence remains separately gated."
