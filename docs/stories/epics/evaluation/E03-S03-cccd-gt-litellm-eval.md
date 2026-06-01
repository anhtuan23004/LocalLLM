# E03-S03 CCCD Ground-Truth LiteLLM Evaluation

## Status

implemented

## Lane

normal

## Product Contract

Evaluation can score a vision LiteLLM Gateway Alias against the CCCD
ground-truth JSONL splits with:

```bash
make eval-cccd-gt MODEL=<alias> SPLIT=all
```

The evaluator sends one image per sample with strict JSON schema
`response_format`, compares the model JSON to ground truth, and writes summary
and per-sample detail artifacts into daily directories under
`evaluation/results/cccd_gt_eval/`.

## Relevant Product Docs

- `docs/product/domains.md` (Evaluation).
- `README.md` (Run Evaluation).
- `docs/runbooks/cccd-gt-evaluation.md`.

## Acceptance Criteria

- `evaluation/scripts/run_cccd_gt_eval.py` reads the front/back CCCD JSONL
  datasets and uses assistant content as ground truth.
- Requests include `response_format` with strict front/back CCCD JSON schemas,
  `temperature=0`, and local images encoded as `data:` URLs.
- Reports include request success, JSON parse success, exact object match,
  per-field accuracy, and latency metrics.
- Detail reports keep ground truth, parsed model output, raw LiteLLM response,
  per-field matches, and request metadata per sample.
- `make eval-cccd-gt MODEL=<alias>` runs the evaluator with a local LiteLLM
  default base URL.

## Design Notes

- The script is host-side because it reads `datasets/` directly from the repo
  root and does not require changing `evaluation/docker-compose.yml`.
- Shared CCCD prompt/schema helpers live in `llm_local.cccd_schema` so dataset
  generation and evaluation use the same contract.
- Scoring compares strings after Unicode NFKC normalization, trimmed and
  collapsed whitespace, and case-insensitive matching; it does not do fuzzy or
  semantic matching beyond that.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python -m unittest evaluation.tests.test_cccd_gt_eval` |
| Integration | `python -m py_compile llm_local/cccd_schema.py datasets/prepare_cccd_qwen3_vl.py evaluation/scripts/run_cccd_gt_eval.py`; dataset regeneration still emits 313 front and 31 back records |
| E2E | Deferred until a Qwen3-VL vision model is running behind LiteLLM |
| Platform | n/a |
| Release | n/a |

## Harness Delta

- Added this story packet.
- Added `E03-S03` to `docs/TEST_MATRIX.md`.
- Updated evaluation docs and Makefile target list.

## Evidence

```bash
$ python -m py_compile llm_local/cccd_schema.py datasets/prepare_cccd_qwen3_vl.py evaluation/scripts/run_cccd_gt_eval.py
# exits 0

$ python -m unittest evaluation.tests.test_cccd_gt_eval
# exits 0; 8 tests run

$ python datasets/prepare_cccd_qwen3_vl.py
# emits 313 front records and 31 back records
```

Runtime LiteLLM proof remains deferred until a configured vision model alias is
available locally.
