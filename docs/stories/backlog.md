# Story Backlog

Derived from spec intake on 2026-05-18. Create story packets when work is
selected, not before.

## Candidate Epics

| Epic | Description | Status |
| --- | --- | --- |
| E01-serving | Model serving: Ollama general LLM + vLLM for Qwen-VL vision models | unsliced |
| E02-training | Fine-tuning environment: Unsloth with Jupyter, GPU, shared models/datasets | unsliced |
| E03-evaluation | Latency benchmarking against serving endpoints via OpenAI-compat API | unsliced |
| E04-observation | Metrics aggregation and visualization from benchmark results | unsliced |
| E05-model-management | Model download, inventory, storage, and cross-service sharing | unsliced |

## First Story Candidates

These are ready to slice into story packets when selected:

- **E01-S01**: Validate Ollama starts, passes healthcheck, responds to chat completion.
- **E01-S02**: Validate Qwen-VL starts with .env config, passes healthcheck.
- **E02-S01**: Validate Unsloth Jupyter accessible and can import unsloth.
- **E03-S01**: Run benchmark against Ollama, verify JSON output schema.
- **E04-S01**: Run observation against existing results, verify CSV + chart output.
- **E05-S01**: Download a small model, verify directory structure and file presence.
- **Cross-S01**: Validate all services reachable on llm-net from evaluation container.
- **Cross-S02**: Add top-level orchestration docker-compose.yml.
- **Cross-S03**: Add GPU availability pre-check script.
- **Cross-S04**: Fix compose-contract drift for Unsloth Ollama reachability and Qwen-VL healthcheck/env configuration.
