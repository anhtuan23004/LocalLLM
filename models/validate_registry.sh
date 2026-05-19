#!/usr/bin/env bash
# models/validate_registry.sh — Validate registry.yaml entries against filesystem.
# Checks that model paths exist and contain expected files.
# Requires: yq (https://github.com/mikefarah/yq)

set -euo pipefail

REGISTRY="${1:-$(dirname "$0")/registry.yaml}"
ERRORS=0

if ! command -v yq &>/dev/null; then
  echo "ERROR: yq not found. Install: brew install yq"
  exit 1
fi

if [ ! -f "$REGISTRY" ]; then
  echo "ERROR: Registry not found: $REGISTRY"
  exit 1
fi

MODEL_COUNT=$(yq '.models | length' "$REGISTRY")
echo "[*] Validating $MODEL_COUNT model(s) from $REGISTRY"
echo ""

for i in $(seq 0 $((MODEL_COUNT - 1))); do
  id=$(yq ".models[$i].id" "$REGISTRY")
  path=$(yq ".models[$i].path" "$REGISTRY")
  format=$(yq ".models[$i].format" "$REGISTRY")

  printf "  %-20s %s ... " "$id" "$path"

  if [ ! -d "$path" ]; then
    echo "MISSING"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Check for expected files based on format
  case "$format" in
    safetensors)
      if ls "$path"/*.safetensors &>/dev/null; then echo "OK"
      else echo "WARN: no .safetensors files"; ERRORS=$((ERRORS + 1)); fi
      ;;
    gguf)
      if ls "$path"/*.gguf &>/dev/null; then echo "OK"
      else echo "WARN: no .gguf files"; ERRORS=$((ERRORS + 1)); fi
      ;;
    *)
      echo "OK (format: $format)"
      ;;
  esac
done

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "[+] All models validated successfully."
else
  echo "[-] $ERRORS issue(s) found."
  exit 1
fi
