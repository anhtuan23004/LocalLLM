# Story Backlog

Derived from spec intake on 2026-05-18. Create story packets when work is
selected, not before.

## Candidate Epics

Statuses in this table are refreshed manually from `docs/TEST_MATRIX.md`; when
they disagree, the matrix is the source of truth.

| Epic | Description | Status |
| --- | --- | --- |
| E01-serving | Model serving: Ollama general LLM + vLLM OpenAI-compatible inference | partially implemented; E01-S02 remains planned and is next priority |
| E02-training | Fine-tuning environment: Unsloth with Jupyter, GPU, shared models/datasets | implemented |
| E03-evaluation | Latency and quality benchmarking against serving endpoints via OpenAI-compat API | implemented |
| E04-observation | Metrics aggregation and visualization from benchmark results | implemented |
| E05-model-management | Model download, inventory, storage, and cross-service sharing | implemented |
| E06-real-time-observability | Prometheus, Grafana, and optional GPU metrics for live inference visibility | implemented |
| E07-litellm-gateway | LiteLLM as one OpenAI-compatible gateway across local runtimes | implemented |
| E08-clients | Programmatic clients that consume LiteLLM for local application workflows | partially implemented |

## Next Selected Story

1. **E01-S02**: Validate vLLM OpenAI-compatible serving.

   Reason: vLLM is a core serving runtime. Later evaluation, observability,
   LiteLLM routing, and client workflows depend on at least one validated
   OpenAI-compatible backend beyond Ollama.

   Story packet:
   `docs/stories/epics/serving/E01-S02-vllm-openai-compatible-serving.md`

## First Story Candidates

These are ready to slice into story packets when selected:

- **E01-S01**: Validate Ollama starts, passes healthcheck, responds to chat completion. _(implemented — see `docs/stories/epics/serving/E01-S01-ollama-chat-completions.md`)_
- **E01-S02**: Validate vLLM starts with .env config, serves the configured model, and passes healthcheck. _(next priority — see `docs/stories/epics/serving/E01-S02-vllm-openai-compatible-serving.md`)_
- **E01-S03**: Add setup for SGLang, llama.cpp, MLX-LM, and non-conflicting host ports. _(implemented — see `docs/stories/epics/serving/E01-S03-serving-runtime-setup.md`)_
- **E02-S01**: Validate Unsloth Jupyter accessible and can import unsloth. _(implemented — see `docs/stories/epics/training/E02-S01-unsloth-jupyter-gpu.md`)_
- **E03-S01**: Run benchmark against Ollama, verify JSON output schema. _(implemented — see `docs/stories/epics/evaluation/E03-S01-benchmark-produces-valid-json.md`)_
- **E03-S02**: Run lm-eval-harness smoke quality eval against vLLM/OpenAI-compatible endpoint. _(implemented — see `docs/stories/epics/evaluation/E03-S02-lm-eval-harness-quality.md`)_
- **E03-S03**: Evaluate CCCD ground-truth OCR outputs through a LiteLLM vision alias. _(implemented — see `docs/stories/epics/evaluation/E03-S03-cccd-gt-litellm-eval.md`)_
- **E04-S01**: Run observation against existing results, verify CSV + chart output. _(implemented — see `docs/stories/epics/observation/E04-S01-observation-produces-csv-chart.md`)_
- **E05-S01**: Download a small model, verify directory structure and file presence. _(implemented — see `docs/stories/epics/model-management/E05-S01-download-model.md`)_
- **E05-S02**: Add model registry YAML and placeholder conversion commands. _(implemented — see `docs/stories/epics/model-management/E05-S02-model-registry.md`)_
- **E05-S03**: Implement HF→GGUF conversion via llama.cpp. _(implemented — see `docs/stories/epics/model-management/E05-S03-hf-to-gguf.md`)_
- **E05-S04**: Implement GGUF→Ollama model import. _(implemented — see `docs/stories/epics/model-management/E05-S04-gguf-to-ollama.md`)_
- **E05-S05**: Validate registry paths and model availability. _(implemented — see `docs/stories/epics/model-management/E05-S05-registry-validation.md`)_
- **E05-S06**: Add serving presets for workflow-level model/runtime switching. _(implemented — see `docs/stories/epics/model-management/E05-S06-serving-presets.md`)_
- **E06-S01**: Add Prometheus + Grafana real-time observability with optional GPU exporter. _(implemented — see `docs/stories/epics/observation/E06-S01-prometheus-grafana-realtime.md`)_
- **Cross-S01**: Validate all services reachable on llm-net from evaluation container. _(implemented — see `docs/stories/epics/cross/Cross-S01-llm-net-reachability.md`)_
- **Cross-S02**: Add top-level Makefile orchestration shortcuts. _(implemented — see `docs/stories/epics/cross/Cross-S02-makefile-orchestration.md`)_
- **Cross-S03**: Add GPU availability pre-check script. _(implemented — see `docs/stories/epics/cross/Cross-S03-runtime-guardrails.md`)_
- **Cross-S04**: Fix compose-contract drift for Unsloth Ollama reachability and vLLM healthcheck/env configuration. _(implemented — see `docs/stories/epics/cross/Cross-S04-compose-contract-drift.md`)_
- **Cross-S05**: Add lightweight smoke regression guard. _(implemented — see `docs/stories/epics/cross/Cross-S05-smoke-regression-guard.md`)_
- **Cross-S06**: Split durable model metadata from local model inventory so
  `make smoke` can pass on a fresh clone or cleaned cache without requiring
  ignored model weight files. _(candidate from architecture audit — see
  `docs/ARCHITECTURE_AUDIT.md`)_
- **Cross-S07**: Centralize runtime contract facts, move `llm-local` behind a
  Python command layer, define executable validation ladder commands, and pin
  runtime image defaults. _(implemented — see
  `docs/stories/epics/cross/Cross-S07-runtime-contract-control-plane.md`)_
- **E07-S01**: Add minimal LiteLLM gateway routing to Ollama. _(implemented — see `docs/stories/epics/serving/E07-S01-minimal-litellm-gateway.md`)_
- **E07-S02**: Add LiteLLM aliases for vLLM, SGLang, llama.cpp, and MLX-LM. _(implemented — see `docs/stories/epics/serving/E07-S02-litellm-multi-runtime-routing.md`)_
- **E07-S03**: Add evaluation target and Makefile benchmark path for LiteLLM. _(implemented — see `docs/stories/epics/evaluation/E07-S03-litellm-evaluation-target.md`)_
- **E07-S04**: Scrape LiteLLM Prometheus metrics and add Grafana gateway panels. _(implemented — see `docs/stories/epics/observation/E07-S04-litellm-observability.md`)_
- **E07-S05**: Add Open WebUI as a client of LiteLLM. _(implemented — see `docs/stories/epics/clients/E07-S05-open-webui-adapter.md`)_
- **E08-S01**: Add one-image OCR extract client API through LiteLLM. _(changed by E08-S02 — see `docs/stories/epics/clients/E08-S01-ocr-extract-client.md`)_
- **E08-S02**: Add public OCR API v1 classify-segment/extract for image and PDF through strict LiteLLM structured output. _(implemented — see `docs/stories/epics/clients/E08-S02-ocr-v1-public-api/overview.md`)_
