#!/usr/bin/env bash
# models/convert.sh — Convert models between formats.
# Usage:
#   ./convert.sh hf2gguf <model-path> [--outtype f16|q8_0|...]
#   ./convert.sh gguf2ollama <gguf-file> [--name model-name]
#
# Prerequisites:
#   hf2gguf:    llama.cpp repo cloned (set LLAMA_CPP_DIR or default: ../llama.cpp)
#   gguf2ollama: ollama CLI installed and server running

set -euo pipefail

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$(dirname "$0")/../llama.cpp}"

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

  local convert_script="$LLAMA_CPP_DIR/convert_hf_to_gguf.py"
  if [ ! -f "$convert_script" ]; then
    echo "ERROR: $convert_script not found."
    echo "Clone llama.cpp: git clone https://github.com/ggerganov/llama.cpp.git"
    echo "Or set LLAMA_CPP_DIR to its location."
    exit 1
  fi

  local outfile="${model_path}/$(basename "$model_path")-${outtype}.gguf"

  echo "[*] Converting: $model_path → $outfile (type: $outtype)"
  python3 "$convert_script" "$model_path" --outtype "$outtype" --outfile "$outfile"
  echo "[+] Output: $outfile"
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
