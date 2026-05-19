# E05-S01 Download Model Script End-to-End

## Status

implemented

## Lane

normal

## Product Contract

`models/download_model.py` downloads a Hugging Face model snapshot into a
model-specific directory under the configured models root.

## Relevant Product Docs

- `docs/product/domains.md` (Model Management).
- `models/registry.yaml`.

## Acceptance Criteria

- The script accepts a Hugging Face repo id and `--dir` output root.
- The script creates a subdirectory named after the repo basename.
- The downloaded directory contains model metadata/tokenizer files and model
  weight files.
- Non-essential formats from the ignore list are excluded.

## Design Notes

- The current validated model is `THUDM/GLM-OCR-2B-1.1`, stored at
  `models/GLM-OCR`.
- This story proves the download path and filesystem layout. Registry metadata
  validation is covered by E05-S05.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | n/a |
| Integration | Downloaded model directory exists with expected files |
| E2E | n/a |
| Platform | n/a |
| Release | n/a |

## Harness Delta

- Added this story packet and updated `docs/TEST_MATRIX.md`.

## Evidence

```bash
$ python models/download_model.py THUDM/GLM-OCR-2B-1.1 --dir models
# downloads to models/GLM-OCR

$ find models/GLM-OCR -maxdepth 1 -type f | sort
models/GLM-OCR/.gitattributes
models/GLM-OCR/README.md
models/GLM-OCR/chat_template.jinja
models/GLM-OCR/config.json
models/GLM-OCR/generation_config.json
models/GLM-OCR/model.safetensors
models/GLM-OCR/preprocessor_config.json
models/GLM-OCR/tokenizer.json
models/GLM-OCR/tokenizer_config.json
```
