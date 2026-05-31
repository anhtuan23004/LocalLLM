#!/usr/bin/env bash
# scripts/smoke.sh — compatibility wrapper for the validation ladder.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  PYTHON="${LLM_LOCAL_PYTHON:-python3}"
fi

exec "$PYTHON" -m llm_local.validation quick "$@"
