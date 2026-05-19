# E05-S02 Model Registry and Conversion Entrypoint

## Status

implemented

## Lane

tiny

## Product Contract

A YAML registry tracks all downloaded models with metadata (repo, format, size,
serving target, quantization variants). A conversion script provides the
command entrypoint for HF→GGUF and GGUF→Ollama pipelines.

## Relevant Product Docs

- `docs/product/domains.md` (Model Management section)

## Acceptance Criteria

- `models/registry.yaml` exists with at least one model entry (GLM-OCR).
- Registry schema includes: id, repo, format, size_gb, path, serving_target, quantizations, downloaded.
- `models/convert.sh` accepts `hf2gguf` and `gguf2ollama` commands.
- Script prints usage and clear errors when required arguments or prerequisites are missing.
- Product docs updated to reference both files.

## Design Notes

- Registry is human-editable YAML, not a database.
- Conversion implementation is owned by E05-S03 and E05-S04.
- The registry itself introduces no new runtime service.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `bash -n models/convert.sh`; missing-command or missing-argument paths print usage/errors |
| Integration | — |
| E2E | — |
| Platform | — |
| Release | — |

## Harness Delta

None.

## Evidence

```bash
$ bash -n models/convert.sh
# exits 0

$ ./models/convert.sh
Usage: ./models/convert.sh <hf2gguf|gguf2ollama> <path> [options]

$ cat models/registry.yaml | head -5
# Model Registry — LLM-Local
# Tracks downloaded models, their formats, and serving targets.

models:
  - id: GLM-OCR
```
