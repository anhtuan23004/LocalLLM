# Test Matrix

This file maps product behavior to proof.

LLM-Local behavior has been defined from the current repository, but proof has
not been recorded yet. Do not mark a row implemented until tests or validation
evidence exist.

## Status Values

| Status | Meaning |
| --- | --- |
| planned | Accepted as intended behavior, not implemented |
| in_progress | Actively being built |
| implemented | Implemented and proof exists |
| changed | Contract changed after earlier implementation |
| retired | No longer part of the product contract |

## Matrix

| Story | Contract | Unit | Integration | E2E | Platform | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E01-S01 | Ollama serves chat completions on llm-net | no | yes | no | no | implemented | docs/stories/epics/serving/E01-S01-ollama-chat-completions.md |
| E01-S02 | vLLM serves configured model through OpenAI-compatible API | no | no | no | no | planned | none |
| E01-S03 | Serving runtime setup exists for SGLang, llama.cpp, MLX-LM, and non-conflicting host ports | yes | yes | no | no | implemented | docs/stories/epics/serving/E01-S03-serving-runtime-setup.md |
| E02-S01 | Unsloth Jupyter accessible with GPU | no | yes | no | yes | implemented | docs/stories/epics/training/E02-S01-unsloth-jupyter-gpu.md |
| E03-S01 | Benchmark produces valid JSON with latency stats | no | yes | no | no | implemented | docs/stories/epics/evaluation/E03-S01-benchmark-produces-valid-json.md |
| E03-S02 | lm-eval-harness quality eval service is configured for OpenAI-compatible endpoint | no | yes | no | no | implemented | docs/stories/epics/evaluation/E03-S02-lm-eval-harness-quality.md |
| E04-S01 | Observation produces CSV summary + latency chart | no | yes | no | no | implemented | docs/stories/epics/observation/E04-S01-observation-produces-csv-chart.md |
| E05-S01 | download_model.py fetches model to correct path | no | yes | no | no | implemented | docs/stories/epics/model-management/E05-S01-download-model.md |
| E05-S02 | Model registry YAML and conversion entrypoint exist | yes | no | no | no | implemented | docs/stories/epics/model-management/E05-S02-model-registry.md |
| E05-S03 | HF weights convert to GGUF through llama.cpp entrypoint | yes | no | no | no | implemented | docs/stories/epics/model-management/E05-S03-hf-to-gguf.md |
| E05-S04 | GGUF files import into Ollama through generated Modelfile | yes | no | no | no | implemented | docs/stories/epics/model-management/E05-S04-gguf-to-ollama.md |
| E05-S05 | Model registry validation checks paths and expected files | yes | yes | no | no | implemented | docs/stories/epics/model-management/E05-S05-registry-validation.md |
| E06-S01 | Prometheus + Grafana provide real-time inference and optional GPU dashboards | yes | yes | no | no | implemented | docs/stories/epics/observation/E06-S01-prometheus-grafana-realtime.md |
| Cross-S01 | All services reachable on llm-net | no | yes | no | yes | implemented | docs/stories/epics/cross/Cross-S01-llm-net-reachability.md |
| Cross-S02 | Makefile orchestration targets work and compose configs validate | yes | yes | no | no | implemented | docs/stories/epics/cross/Cross-S02-makefile-orchestration.md |
| Cross-S04 | Compose configuration matches product contracts | n/a | yes | no | no | implemented | docs/stories/epics/cross/Cross-S04-compose-contract-drift.md |
| Cross-S05 | Smoke script guards compose, scripts, registry, and dashboard artifacts | yes | yes | no | no | implemented | docs/stories/epics/cross/Cross-S05-smoke-regression-guard.md |

## Evidence Rules

- Unit proof covers pure domain and application rules.
- Integration proof covers backend enforcement, data integrity, provider
  behavior, jobs, or service contracts.
- E2E proof covers user-visible browser flows.
- Platform proof covers only shell, deployment, mobile, desktop, or runtime
  behavior that cannot be proven in lower layers.
- A story can be implemented without every proof column if the story packet
  explains why.
