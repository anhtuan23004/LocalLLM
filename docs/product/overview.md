# Product Overview — LLM-Local

## Vision

A self-contained local infrastructure for running, fine-tuning, evaluating, and
monitoring large language models on personal GPU hardware.

## Users

- ML engineers experimenting with open-weight models locally.
- Developers integrating LLM capabilities into applications.
- Researchers benchmarking model performance before cloud deployment.

## Domain Map

```text
┌─────────────────────────────────────────────────────┐
│                   llm-net (Docker)                   │
├──────────┬──────────┬─────────────┬─────────────────┤
│ Serving  │ Training │ Evaluation  │   Observation   │
│          │          │             │                 │
│ Ollama   │ Unsloth  │ Benchmark   │ Metrics + Charts│
│ vLLM     │ (Jupyter)│ (lm-eval)   │ (matplotlib)    │
├──────────┴──────────┴─────────────┴─────────────────┤
│              Shared Resources                        │
│  models/  datasets/  results/  dashboards/          │
└─────────────────────────────────────────────────────┘
```

## Key Properties

- Each domain is an independent Docker Compose stack.
- All stacks join a shared external network (`llm-net`).
- Model weights are shared via bind-mounted `models/` directory.
- No cloud dependencies at runtime; Hugging Face Hub used only for downloads.
- GPU resources allocated per-service via Docker device reservations.

## Current State

Working infrastructure exists for all four domains. No orchestration layer,
no CI, no automated validation pipeline yet.
