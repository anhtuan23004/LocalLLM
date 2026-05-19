#!/usr/bin/env bash
# models/convert.sh — Convert models between formats.
# Usage:
#   ./convert.sh hf2gguf <model-path> [--outtype f16|q8_0|...]
#   ./convert.sh gguf2ollama <gguf-file> [--name model-name]
#
# Prerequisites:
#   hf2gguf:    llama.cpp auto-cloned into vendor/llama.cpp on first use
#               Python deps installed with: uv sync --extra convert
#   gguf2ollama: ollama CLI installed and server running

set -euo pipefail

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$(dirname "$0")/../vendor/llama.cpp}"

python_cmd() {
  if [ -n "${PYTHON_BIN:-}" ]; then
    printf '%s\n' "$PYTHON_BIN"
  elif command -v uv >/dev/null 2>&1; then
    printf '%s\n' "uv run python"
  else
    printf '%s\n' "python3"
  fi
}

check_hf2gguf_python_deps() {
  local python_bin="$1"
  local missing

  missing="$($python_bin - <<'PY'
import importlib.util

missing = [
    module
    for module in ("gguf", "torch")
    if importlib.util.find_spec(module) is None
]
print(" ".join(missing))
raise SystemExit(1 if missing else 0)
PY
)" || {
    echo "ERROR: missing Python conversion dependencies: $missing"
    echo "Install them with: uv sync --extra convert"
    echo "Or set PYTHON_BIN to a Python environment that has: gguf torch"
    exit 1
  }
}

usage() {
  echo "Usage: $0 <hf2gguf|gguf2ollama> <path> [options]"
  echo ""
  echo "Commands:"
  echo "  hf2gguf <model-dir> [--outtype TYPE]   Convert HF safetensors to GGUF"
  echo "  gguf2ollama <gguf-file> [--name NAME]  Import GGUF into Ollama"
  exit 1
}

cmd_hf2gguf() {
  if [ $# -lt 1 ]; then
    echo "ERROR: missing model directory."
    usage
  fi

  local model_path="$1"; shift
  local outtype="f16"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --outtype)
        if [ $# -lt 2 ]; then
          echo "ERROR: --outtype requires a value."
          exit 1
        fi
        outtype="$2"
        shift 2
        ;;
      *) echo "Unknown option: $1"; exit 1 ;;
    esac
  done

  local python_bin
  python_bin="$(python_cmd)"
  check_hf2gguf_python_deps "$python_bin"

  local convert_script="$LLAMA_CPP_DIR/convert_hf_to_gguf.py"
  if [ ! -f "$convert_script" ]; then
    echo "[*] llama.cpp not found. Cloning into $LLAMA_CPP_DIR (shallow)..."
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git "$LLAMA_CPP_DIR"
  fi

  local outfile="${model_path}/$(basename "$model_path")-${outtype}.gguf"

  echo "[*] Converting: $model_path → $outfile (type: $outtype)"
  $python_bin "$convert_script" "$model_path" --outtype "$outtype" --outfile "$outfile"
  echo "[+] Output: $outfile"

  # Update sidecar with quantization info
  local sidecar="$model_path/model.yaml"
  if [ -f "$sidecar" ]; then
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local root_dir
    root_dir="$(dirname "$script_dir")"
    "$root_dir/.venv/bin/python" - "$sidecar" "$outtype" <<'PYEOF'
import sys
from ruamel.yaml import YAML
yaml = YAML()
yaml.default_flow_style = False
sidecar_path, quant = sys.argv[1], sys.argv[2]
with open(sidecar_path) as f:
    data = yaml.load(f)
quants = data.setdefault("quantizations", [])
if quant not in quants:
    quants.append(quant)
# Add gguf targets if not present
targets = data.setdefault("serving_targets", [])
for t in ["llama.cpp", "ollama"]:
    if t not in targets:
        targets.append(t)
data["serving_targets"] = targets
with open(sidecar_path, "w") as f:
    yaml.dump(data, f)
print(f"[+] Updated sidecar: added quantization '{quant}', targets: {targets}")
PYEOF
  fi
}

cmd_gguf2ollama() {
  if [ $# -lt 1 ]; then
    echo "ERROR: missing GGUF file."
    usage
  fi

  local gguf_file="$1"; shift
  local model_name=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --name)
        if [ $# -lt 2 ]; then
          echo "ERROR: --name requires a value."
          exit 1
        fi
        model_name="$2"
        shift 2
        ;;
      *) echo "Unknown option: $1"; exit 1 ;;
    esac
  done

  if [ ! -f "$gguf_file" ]; then
    echo "ERROR: GGUF file not found: $gguf_file"
    exit 1
  fi

  if ! command -v ollama &>/dev/null; then
    echo "ERROR: ollama CLI not found. Install from https://ollama.com"
    exit 1
  fi

  # Default name from filename without extension
  if [ -z "$model_name" ]; then
    model_name="$(basename "$gguf_file" .gguf)"
  fi

  local modelfile
  modelfile="$(mktemp)"
  trap 'rm -f "$modelfile"' RETURN
  echo "FROM $gguf_file" > "$modelfile"

  echo "[*] Creating Ollama model: $model_name from $gguf_file"
  ollama create "$model_name" -f "$modelfile"
  echo "[+] Model available: ollama run $model_name"
}

# --- Main ---
CMD="${1:-}"
[ -z "$CMD" ] && usage
shift

case "$CMD" in
  hf2gguf)    cmd_hf2gguf "$@" ;;
  gguf2ollama) cmd_gguf2ollama "$@" ;;
  *)          usage ;;
esac
