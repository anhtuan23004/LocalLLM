# Story Backlog

Derived from spec intake on 2026-05-18. Create story packets when work is
selected, not before.

## Candidate Epics

| Epic | Description | Status |
| --- | --- | --- |
| E01-serving | Model serving: Ollama general LLM + vLLM OpenAI-compatible inference | infra exists, unvalidated |
| E02-training | Fine-tuning environment: Unsloth with Jupyter, GPU, shared models/datasets | infra exists, unvalidated |
| E03-evaluation | Latency and quality benchmarking against serving endpoints via OpenAI-compat API | partially validated (E03-S02) |
| E04-observation | Metrics aggregation and visualization from benchmark results | infra exists (real-time + batch), unvalidated |
| E05-model-management | Model download, inventory, storage, and cross-service sharing | sliced, mostly implemented |
| E06-real-time-observability | Prometheus, Grafana, and optional GPU metrics for live inference visibility | sliced |

## First Story Candidates

These are ready to slice into story packets when selected:

- **E01-S01**: Validate Ollama starts, passes healthcheck, responds to chat completion. _(implemented — see `docs/stories/epics/serving/E01-S01-ollama-chat-completions.md`)_
- **E01-S02**: Validate vLLM starts with .env config, serves the configured model, and passes healthcheck.
- **E02-S01**: Validate Unsloth Jupyter accessible and can import unsloth. _(implemented — see `docs/stories/epics/training/E02-S01-unsloth-jupyter-gpu.md`)_
- **E03-S01**: Run benchmark against Ollama, verify JSON output schema. _(implemented — see `docs/stories/epics/evaluation/E03-S01-benchmark-produces-valid-json.md`)_
- **E03-S02**: Run lm-eval-harness smoke quality eval against vLLM/OpenAI-compatible endpoint.
- **E04-S01**: Run observation against existing results, verify CSV + chart output. _(implemented — see `docs/stories/epics/observation/E04-S01-observation-produces-csv-chart.md`)_
- **E05-S01**: Download a small model, verify directory structure and file presence. _(implemented — see `docs/stories/epics/model-management/E05-S01-download-model.md`)_
- **E05-S02**: Add model registry YAML and placeholder conversion commands. _(implemented — see `docs/stories/epics/model-management/E05-S02-model-registry.md`)_
- **E05-S03**: Implement HF→GGUF conversion via llama.cpp. _(implemented — see `docs/stories/epics/model-management/E05-S03-hf-to-gguf.md`)_
- **E05-S04**: Implement GGUF→Ollama model import. _(implemented — see `docs/stories/epics/model-management/E05-S04-gguf-to-ollama.md`)_
- **E05-S05**: Validate registry paths and model availability. _(implemented — see `docs/stories/epics/model-management/E05-S05-registry-validation.md`)_
- **E06-S01**: Add Prometheus + Grafana real-time observability with optional GPU exporter. _(implemented — see `docs/stories/epics/observation/E06-S01-prometheus-grafana-realtime.md`)_
- **Cross-S01**: Validate all services reachable on llm-net from evaluation container. _(implemented — see `docs/stories/epics/cross/Cross-S01-llm-net-reachability.md`)_
- **Cross-S02**: Add top-level Makefile orchestration shortcuts. _(implemented — see `docs/stories/epics/cross/Cross-S02-makefile-orchestration.md`)_
- **Cross-S03**: Add GPU availability pre-check script.
- **Cross-S04**: Fix compose-contract drift for Unsloth Ollama reachability and vLLM healthcheck/env configuration. _(implemented — see `docs/stories/epics/cross/Cross-S04-compose-contract-drift.md`)_
- **Cross-S05**: Add lightweight smoke regression guard. _(implemented — see `docs/stories/epics/cross/Cross-S05-smoke-regression-guard.md`)_
