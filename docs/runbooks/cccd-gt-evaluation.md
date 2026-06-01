# CCCD Ground-Truth Evaluation

Use this runbook to score a vision model served behind LiteLLM against the CCCD
ground-truth JSONL datasets.

## Prerequisites

- `datasets/cccd_qwen3_vl/front/train.jsonl` and
  `datasets/cccd_qwen3_vl/back/train.jsonl` exist.
- LiteLLM is reachable from the host at `http://localhost:18040/v1`.
- `MODEL` is a LiteLLM alias backed by a vision-capable model.

## Smoke

```bash
make eval-cccd-gt MODEL=local-vllm SPLIT=front LIMIT=1
```

## Full Run

```bash
make eval-cccd-gt MODEL=local-vllm SPLIT=all
```

Override the LiteLLM endpoint when needed:

```bash
make eval-cccd-gt MODEL=local-vllm CCCD_EVAL_BASE_URL=http://localhost:18040/v1
```

## Outputs

Each run writes into a date directory under `evaluation/results/cccd_gt_eval/`
with timestamped files:

- `<model>_<HHMMSS>_summary.json`: overall and split-level accuracy, parse success, request
  success, and latency metrics.
- `<model>_<HHMMSS>_details.json`: all per-request detail records when
  `SPLIT=all`.
- `front/<model>_<HHMMSS>_details.json`: one debug record per front-side sample.
- `back/<model>_<HHMMSS>_details.json`: one debug record per back-side sample.

The evaluator compares string values after Unicode NFKC normalization, trimmed
and collapsed whitespace, and case-insensitive matching. It does not parse or
reformat dates beyond those string normalizations.
Each detail record includes `expected`, `predicted`, `raw_response`,
`field_matches`, request status, parse/schema status, error, and latency.
