# E05-S03 HF→GGUF Conversion via llama.cpp

## Status

implemented

## Lane

tiny

## Product Contract

`models/convert.sh hf2gguf <model-dir>` converts HuggingFace safetensors
weights to GGUF format using llama.cpp's `convert_hf_to_gguf.py`. Supports
`--outtype` for quantization selection (default: f16).

## Relevant Product Docs

- `docs/product/domains.md` (Model Management)

## Acceptance Criteria

- `convert.sh hf2gguf` shallow-clones llama.cpp into `vendor/llama.cpp` on first use.
- Checks Python conversion dependencies (`gguf`, `torch`) before cloning or running conversion.
- Calls `convert_hf_to_gguf.py` with correct `--outtype` and `--outfile`.
- Output GGUF placed inside the model directory as `<name>-<type>.gguf`.
- `LLAMA_CPP_DIR` env var overrides default llama.cpp path.
- Exits with clear error if prerequisites missing.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `bash -n models/convert.sh`; missing Python conversion deps produce clear install instructions |
| Integration | With `uv sync --extra convert`, llama.cpp is shallow-cloned and a small model converts to GGUF |

## Evidence

```bash
$ bash -n models/convert.sh
# exits 0

$ LLAMA_CPP_DIR=/tmp/vendor/llama.cpp ./models/convert.sh hf2gguf /tmp/fake
ERROR: missing Python conversion dependencies: torch
Install them with: uv sync --extra convert
```
