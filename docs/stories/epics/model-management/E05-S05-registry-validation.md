# E05-S05 Registry Validation Script

## Status

implemented

## Lane

tiny

## Product Contract

`models/validate_registry.sh` parses `models/registry.yaml` and verifies each
model entry has a valid filesystem path containing the expected files for its
declared format.

## Relevant Product Docs

- `docs/product/domains.md` (Model Management)

## Acceptance Criteria

- Reads registry.yaml (default or passed as argument).
- For each model: checks path exists and contains format-appropriate files.
- `safetensors` format → expects `.safetensors` files.
- `gguf` format → expects `.gguf` files.
- Prints per-model status (OK / MISSING / WARN).
- Exits 0 if all pass, exits 1 if any issues found.
- Requires `yq`; exits with install instructions if missing.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Script exits 1 with clear error when yq is missing |
| Integration | With yq installed, validates GLM-OCR entry as OK |

## Evidence

```bash
$ ./models/validate_registry.sh
[*] Validating 1 model(s) from ./models/registry.yaml

  GLM-OCR              models/GLM-OCR ... OK

[+] All models validated successfully.
```
