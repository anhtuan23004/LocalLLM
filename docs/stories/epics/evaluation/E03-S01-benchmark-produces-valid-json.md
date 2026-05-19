# E03-S01 Benchmark produces valid JSON

## Status

implemented

## Lane

normal

## Product Contract

Benchmark script produces valid JSON with latency statistics when executing against a serving endpoint.

## Relevant Product Docs

- `docs/product/overview.md`

## Acceptance Criteria

- `evaluation` compose service correctly sends requests to the given endpoint.
- Produces valid JSON structure saving requests detail and aggregate latency under `/app/results/`.

## Design Notes

- Commands: `docker compose run --rm evaluation --endpoint http://ollama:11434 --model-name qwen2.5:0.5b --num-requests 3`
- Fix applied to `evaluation/Dockerfile` to remove pinned non-existent version of `lm-eval` and bump.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | |
| Integration | script completes with exit code 0 and json file is written |
| E2E | |
| Platform | |
| Release | |

## Harness Delta

Edited evaluation Dockerfile to fix `lm-eval[openai]` version.

## Evidence

Ran:
```
cd evaluation
docker compose run --rm evaluation --endpoint http://ollama:11434 --model-name qwen2.5:0.5b --num-requests 3
```
JSON file with average latency written to `evaluation/results/benchmark_qwen2.5:0.5b_*.json`.
