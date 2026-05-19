# Cross-S05 Smoke Regression Guard

## Status

implemented

## Lane

tiny

## Product Contract

A top-level smoke script verifies the repository's configuration, scripts, and
tracked dashboard artifacts without requiring heavy GPU services to be running.
Runtime endpoint checks remain available as an explicit opt-in mode.

## Relevant Product Docs

- `README.md` (common validation commands).
- `Makefile` (`smoke` target).
- `docs/TEST_MATRIX.md` (Cross-S05 proof row).

## Acceptance Criteria

- `scripts/smoke.sh` exists and is executable.
- Default `./scripts/smoke.sh` checks compose config, model registry,
  shell-script syntax, Grafana dashboard JSON, and `make help`.
- Default smoke does not require Ollama, vLLM, Prometheus, or Grafana to be
  running.
- `./scripts/smoke.sh --runtime` checks `llm-net`, running service health, and
  local inference/observability endpoints.
- `make smoke` runs the default lightweight smoke.

## Design Notes

- Keep default smoke cheap and deterministic so agents can run it after small
  changes.
- Runtime checks are useful on a prepared workstation, but should not block
  documentation/configuration-only work.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `bash -n scripts/smoke.sh` passes |
| Integration | `./scripts/smoke.sh` exits 0 |
| E2E | n/a |
| Platform | `./scripts/smoke.sh --runtime` deferred to hosts with live services |
| Release | n/a |

## Harness Delta

- Added a cheap regression guard for future agent changes.

## Evidence

```bash
$ bash -n scripts/smoke.sh
# exits 0

$ ./scripts/smoke.sh
=== Compose Configs ===
  ✓ serving/ollama
  ✓ serving/vllm
  ✓ training/unsloth
  ✓ evaluation
  ✓ observation
...
=== Runtime Checks ===
  skipped (run ./scripts/smoke.sh --runtime to check live services)

Results: 15 passed, 0 failed
```
