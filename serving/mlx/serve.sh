#!/usr/bin/env bash
# Start an MLX-LM OpenAI-compatible server on Apple Silicon.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$SCRIPT_DIR/.env"
  set +a
fi

MLX_MODEL="${MLX_MODEL:-mlx-community/Mistral-7B-Instruct-v0.3-4bit}"
MLX_HOST="${MLX_HOST:-0.0.0.0}"
MLX_PORT="${MLX_PORT:-18081}"
MLX_EXTRA_ARGS="${MLX_EXTRA_ARGS:-}"

if ! command -v mlx_lm.server >/dev/null 2>&1; then
  echo "ERROR: mlx_lm.server not found. Install with: pip install mlx-lm"
  exit 1
fi

exec mlx_lm.server \
  --model "$MLX_MODEL" \
  --host "$MLX_HOST" \
  --port "$MLX_PORT" \
  $MLX_EXTRA_ARGS
