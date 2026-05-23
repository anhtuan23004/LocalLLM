# E01-S03 Serving Runtime Setup

## Status

implemented

## Lane

normal

## Product Contract

Serving runtime setup exists for vLLM, SGLang, llama.cpp, Ollama, and host-side
MLX-LM. Docker-backed services expose non-conflicting host ports through
per-service `.env.example` files while preserving their runtime/container
ports.

## Relevant Product Docs

- `docs/product/domains.md` (Serving).
- `docs/ARCHITECTURE.md` (Topology).

## Acceptance Criteria

- SGLang has `serving/sglang/docker-compose.yml`, `.env.example`, and README.
- llama.cpp has `serving/llama.cpp/docker-compose.yml`, `.env.example`, and README.
- MLX-LM has `serving/mlx/serve.sh`, `.env.example`, and README.
- Ollama, vLLM, SGLang, llama.cpp, and MLX-LM use distinct default host ports.
- `make validate-compose` validates all Docker-backed serving compose files.
- `./scripts/smoke.sh` includes the new serving compose files.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `bash -n serving/mlx/serve.sh` |
| Integration | `make validate-compose`; `./scripts/smoke.sh` |
| E2E | n/a |
| Platform | Runtime startup deferred to target hosts with matching GPU/Metal support |
| Release | n/a |

## Evidence

```bash
$ make validate-compose
All compose configs valid.

$ ./scripts/smoke.sh
=== Compose Configs ===
  ✓ serving/ollama
  ✓ serving/vllm
  ✓ serving/sglang
  ✓ serving/llama.cpp
...
Results: 18 passed, 0 failed
```

