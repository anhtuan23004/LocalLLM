# LLM-Local Plan

Updated: 2026-05-18

## Current State

Infrastructure complete. 12/16 test matrix rows validated. Tooling layer
(registry, conversion, Makefile, CLI, smoke test, observability) is solid.
Core loop (serve → benchmark → observe) proven for Ollama.

## Immediate Fixes

| Item | Description |
| --- | --- |
| CLI eval routing | `./llm-local eval run` should accept `--endpoint` instead of hardcoding Ollama |
| Smoke false positive | Remove redundant `curl` checks; rely on `docker inspect` for health |
| GPU guard (Cross-S03) | Enforce decision 0005 — warn/block conflicting GPU services |

## Phase 1 — Prove It Works (next session)

Goal: move every epic from "unvalidated" to "validated." Test matrix → 16/16.

| Story | What it proves | Effort |
| --- | --- | --- |
| E01-S02 | vLLM serves on hardware | 15 min |
| E02-S01 | Unsloth Jupyter loads with GPU | 10 min |
| Cross-S01 | All containers reachable on llm-net | 10 min |
| E05-S01 | Download script works end-to-end | 10 min |

## Phase 2 — Real Usage (this week)

Shift from infrastructure to workflow. Pick one concrete task and execute
the full pipeline:

1. Download a model (`./llm-local model download`)
2. Fine-tune on custom dataset (Unsloth Jupyter)
3. Convert to GGUF (`./llm-local model convert hf2gguf`)
4. Import to Ollama (`./llm-local model convert gguf2ollama`)
5. Benchmark baseline vs fine-tuned (`make benchmark-ollama`)
6. Record results in observation

Document gaps discovered during execution.

## Phase 3 — Middleware Layer (next sprint)

| Component | Purpose | Effort |
| --- | --- | --- |
| LiteLLM Proxy | Single OpenAI-compat endpoint routing to all backends | Small |
| Open WebUI | Interactive chat UI, conversation history, multi-model | Small |
| Qdrant | Vector store for RAG workflows | Medium |

Each is one container on `llm-net`. LiteLLM + Open WebUI = immediate
usability for anyone on local network.

## Phase 4 — Automation & Guards (ongoing)

| Item | Purpose |
| --- | --- |
| Cross-S03: GPU pre-check | Runtime enforcement of GPU budget (decision 0005) |
| Runtime-aware model registry | `download_model.py` writes sidecars and refreshes `registry.yaml` with vLLM, SGLang, llama.cpp, Ollama, and MLX targets |
| Benchmark regression | Store baseline scores, alert on degradation |
| Scheduled smoke | cron/launchd runs `make smoke` daily |

## Non-Goals (current phase)

- Multi-node / cloud deployment
- CI/CD pipeline
- Orchestration beyond Makefile
- Production SLA tooling

## Success Criteria

- [ ] All 16 test matrix rows implemented
- [ ] One complete fine-tune → serve → eval workflow documented
- [ ] LiteLLM + Open WebUI running on llm-net
- [ ] GPU conflicts prevented at runtime
- [ ] Smoke test passes with all services up
