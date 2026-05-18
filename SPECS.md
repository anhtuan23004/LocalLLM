# SPECS — LLM-Local

## Purpose

Self-contained local infrastructure for serving, fine-tuning, evaluating, and
monitoring large language models on personal NVIDIA GPU hardware.

## Target Users

- ML engineers experimenting with open-weight models locally.
- Developers integrating LLM capabilities into applications.
- Researchers benchmarking model performance before cloud deployment.

## System Requirements

- NVIDIA GPU workstation with Docker and NVIDIA Container Toolkit.
- Docker Compose v2+.
- Shared external Docker network (`llm-net`).
- Python 3.11+ (for host-side scripts).

## Domains

### 1. Serving

Expose LLM inference via OpenAI-compatible REST APIs.

| Service | Engine | Port | API |
| --- | --- | --- | --- |
| Ollama | ollama/ollama | 11434 | Ollama + OpenAI-compat |
| Qwen-VL | vllm/vllm-openai | 8000 | OpenAI-compat |

### 2. Training

GPU-accelerated fine-tuning via Jupyter Lab (Unsloth).

| Service | Port | Interface |
| --- | --- | --- |
| Unsloth | 8888 | Jupyter Lab |

### 3. Evaluation

Benchmark serving endpoints for latency and correctness.

- CLI-driven (`run_benchmark.py`).
- Outputs per-run JSON to `evaluation/results/`.
- Configurable endpoint, model, request count, prompt.

### 4. Observation

Aggregate benchmark results into reports and charts.

- Reads `benchmark_*.json` from evaluation results.
- Produces `metrics_summary.csv` and `latency_chart.png`.

### 5. Model Management

Download and share Hugging Face model weights.

- CLI tool: `models/download_model.py`.
- Shared `models/` directory bind-mounted into serving and training.

## Architecture Constraints

- Each domain is an independent Docker Compose stack.
- All stacks join the shared `llm-net` bridge network.
- No cloud dependencies at runtime (Hugging Face Hub for downloads only).
- GPU allocation via Docker device reservations.
- Configuration via `.env` files and CLI arguments.
- No hard inter-service startup dependencies.

## Non-Goals (current phase)

- Orchestration layer across stacks.
- CI/CD pipeline.
- Automated validation suite.
- Multi-node or cloud deployment.
- Real-time monitoring (Prometheus/Grafana deferred).

## Success Criteria

- Any serving endpoint reachable from other containers via `llm-net`.
- Benchmark produces valid JSON with latency statistics.
- Observation generates summary CSV and chart from benchmark data.
- Model download script fetches weights without manual intervention.
- Training environment can load shared models and datasets.
