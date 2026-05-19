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

- `convert.sh hf2gguf` validates llama.cpp directory exists before running.
- Calls `convert_hf_to_gguf.py` with correct `--outtype` and `--outfile`.
- Output GGUF placed inside the model directory as `<name>-<type>.gguf`.
- `LLAMA_CPP_DIR` env var overrides default llama.cpp path.
- Exits with clear error if prerequisites missing.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `convert.sh hf2gguf /nonexistent` exits 1 with error about missing llama.cpp |
| Integration | With llama.cpp cloned, converts a small model to GGUF |

## Evidence

```bash
$ ./models/convert.sh hf2gguf /tmp/fake
ERROR: .../llama.cpp/convert_hf_to_gguf.py not found.
Clone llama.cpp: git clone https://github.com/ggerganov/llama.cpp.git
Or set LLAMA_CPP_DIR to its location.
```
