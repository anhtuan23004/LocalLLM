# E03-S02 Add lm-eval-harness Quality Evaluation

## Status

implemented

## Lane

normal

## Product Contract

Evaluation supports a quality benchmark path using EleutherAI
lm-evaluation-harness against local OpenAI-compatible serving endpoints.
Latency benchmarking remains available through `run_benchmark.py`.

## Relevant Product Docs

- `docs/product/domains.md` (Evaluation).
- `docs/ARCHITECTURE.md` (Docker Compose services and shared results).
- `docs/TEST_MATRIX.md` (E03-S02 proof row).

## Acceptance Criteria

- `evaluation/Dockerfile` installs lm-eval with OpenAI-compatible API support.
- `evaluation/docker-compose.yml` defines an `lm-eval` service under the
  `quality` profile.
- `evaluation/scripts/run_lm_eval.sh` runs `lm_eval` against a configurable
  OpenAI-compatible endpoint and writes output to
  `evaluation/results/lm-eval/`.
- Defaults are bounded for the 1 GPU / 12GB VRAM target:
  `LM_EVAL_BATCH_SIZE=1`, `LM_EVAL_LIMIT=10`, and one concurrent request.
- Existing latency benchmark entrypoint remains unchanged for the
  `evaluation` service.

## Design Notes

- Use `local-chat-completions` by default because vLLM exposes an
  OpenAI-compatible chat completions endpoint.
- Install `lm-eval[api]==0.4.12`;
- Use `--apply_chat_template` so instruct/chat models can be evaluated through
  the harness.
- Keep quality evaluation separate from latency benchmarking because it pulls
  datasets and has different runtime/proof characteristics.
- The default smoke task is `gsm8k`; operators can override it with
  `LM_EVAL_TASKS`.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | n/a (compose/script integration only) |
| Integration | `docker compose --profile quality -f evaluation/docker-compose.yml config` resolves the `lm-eval` service and script defaults; `sh -n evaluation/scripts/run_lm_eval.sh` passes |
| E2E | n/a until a serving endpoint is running |
| Platform | Full run deferred to a GPU host with vLLM up: `docker compose --profile quality run --rm lm-eval` |
| Release | n/a |

## Harness Delta

- No harness process changes required.

## Evidence

```text
$ docker compose --profile quality -f evaluation/docker-compose.yml config
services:
  lm-eval:
    entrypoint:
      - /app/scripts/run_lm_eval.sh
    environment:
      LM_EVAL_BASE_URL: http://vllm:8000/v1/chat/completions
      LM_EVAL_BATCH_SIZE: "1"
      LM_EVAL_LIMIT: "10"
      LM_EVAL_MODEL: Qwen/Qwen3-VL-4B-Instruct
      LM_EVAL_MODEL_TYPE: local-chat-completions
      LM_EVAL_OUTPUT_PATH: /app/results/lm-eval
      LM_EVAL_TASKS: gsm8k

$ sh -n evaluation/scripts/run_lm_eval.sh
# exits 0

$ python3 -m pip install --dry-run --no-cache-dir "lm-eval[api]==0.4.12"
# resolves lm_eval-0.4.12 and API backend dependencies without a missing-version error
```

Full quality run remains deferred until vLLM is running on the target host.
