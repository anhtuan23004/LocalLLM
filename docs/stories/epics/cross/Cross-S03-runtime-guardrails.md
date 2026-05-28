# Cross-S03 Runtime Guardrails

## Status

implemented

## Lane

normal

## Product Contract

Runtime startup fails early for common local workstation mistakes before Docker
pulls a heavy image or starts a GPU process:

- GPU-heavy services follow `docs/decisions/0005-gpu-budget-allocation.md`.
- Host port conflicts are detected before startup.
- Existing container health/state is surfaced during runtime smoke.
- Model registry targets must be compatible with the model file format.

## Relevant Product Docs

- `docs/decisions/0005-gpu-budget-allocation.md`
- `docs/product/domains.md`
- `docs/TEST_MATRIX.md`

## Acceptance Criteria

- `./llm-local guardrails --all` checks known service ports, running service
  health/state, GPU contention, and configured local model/runtime compatibility.
- `./llm-local serve <runtime> up`, `./llm-local webui up`, and
  `./llm-local train up` run guardrails before startup.
- `./llm-local model validate` fails when a registry entry targets an
  incompatible runtime for its model format.
- `./llm-local model select <id> --runtime <runtime>` fails before editing
  runtime `.env` when the selected model format is incompatible with that
  runtime.
- `./llm-local smoke --runtime` includes guardrail and service health checks.

## Design Notes

- `scripts/preflight.py` owns startup guardrails so the CLI, Makefile, and smoke
  tests share one implementation.
- GPU checks enforce decision 0005 conservatively: single-GPU hosts cannot start
  another GPU-heavy runtime while one is running, and `count: all` style services
  cannot overlap with other GPU services.
- Model compatibility is intentionally simple and registry-based:
  `safetensors`/`pytorch` target vLLM, SGLang, and MLX; `gguf` targets
  llama.cpp and Ollama.
- Runtime model paths for Docker-backed serving must use mounted container
  paths under `/models/...`. llama.cpp explicit `.gguf` file paths are accepted
  even when the parent model directory also has a sidecar for non-GGUF serving.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `uv run python -m py_compile scripts/preflight.py models/validate_registry.py models/manage.py` |
| Integration | `./llm-local model validate`; `./llm-local guardrails --all`; `./llm-local smoke` |
| E2E | Not required; this is a CLI/runtime guardrail |
| Platform | Full GPU contention behavior requires a Linux NVIDIA host with running GPU services |
| Release | `make validate`; `./llm-local smoke` |

## Harness Delta

Cross-S03 is now tracked in `docs/TEST_MATRIX.md` and linked from
`docs/stories/backlog.md`.

## Evidence

Validation was run after implementation:

```bash
uv run python -m py_compile scripts/preflight.py models/validate_registry.py models/manage.py
./llm-local model validate
./llm-local smoke
make validate
```

An invalid temporary registry with `format: safetensors` targeting `llama.cpp`
was rejected with:

```text
WARN: safetensors incompatible with target(s): llama.cpp; allowed: mlx, sglang, vllm
```

The live guardrail path was also exercised on the current workstation:

```bash
./llm-local guardrails open-webui
# FAIL: open-webui: host port 18088 is already in use before open-webui is running

./llm-local smoke --runtime
# exits non-zero because live Ollama/vLLM/Prometheus/Grafana containers are not
# running and guardrails detect the Open WebUI port conflict.
```

Follow-up validation for the mounted-path guardrail:

```bash
uv run python -m py_compile scripts/preflight.py
./llm-local guardrails llama.cpp
# OK after local llama.cpp .env uses /models/... paths for the GGUF and mmproj files.
```
