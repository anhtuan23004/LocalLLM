# Product Domains — LLM-Local

## Serving

Expose LLM inference endpoints on the local network.

### Services

| Service | Engine | API | Port | GPU |
| --- | --- | --- | --- | --- |
| Ollama | ollama/ollama:latest | Ollama API + OpenAI-compat | 11434 | all |
| vLLM | vllm/vllm-openai | OpenAI-compatible | 8000 | GPU 0 by default |

### Contracts

- Ollama exposes `/api/generate`, `/api/chat`, and OpenAI-compatible `/v1/chat/completions`.
- vLLM exposes `/v1/chat/completions` and `/health`.
- Both join `llm-net` and are reachable by container name from other services.
- Healthchecks defined: Ollama via `ollama list`, vLLM via curl `/health`.

### Configuration

- Ollama: stateless config, model data in `ollama_data` Docker volume.
- vLLM: `.env` file controls model path, served model name, GPU allocation, memory utilization, and tensor parallelism.

---

## Training

Fine-tune models using GPU-accelerated Jupyter environment.

### Services

| Service | Engine | Interface | Port | GPU |
| --- | --- | --- | --- | --- |
| Unsloth | unsloth/unsloth:latest | Jupyter Lab | 8888 | all |

### Contracts

- Jupyter accessible at `localhost:8888` with password auth.
- SSH available on port 2222.
- Secondary API port on 8001 (maps to container 8000).
- Mounts `models/` and `datasets/` from repo root for shared access.
- Work directory persisted at `training/unsloth/work/`.
- Can reach Ollama at `http://ollama:11434` via `llm-net`.

---

## Evaluation

Benchmark model serving endpoints for latency and correctness.

### Services

| Service | Base | Tools | Output |
| --- | --- | --- | --- |
| evaluation | python:3.11-slim | requests, pandas, lm-eval | evaluation/results/*.json |

### Contracts

- Runs `run_benchmark.py` as entrypoint with CLI args: `--endpoint`, `--model-name`, `--num-requests`, `--prompt`.
- Sends N chat completion requests, records per-request latency.
- Outputs JSON with summary stats (avg/min/max latency, success count).
- Results saved to `evaluation/results/` (bind-mounted).
- Reaches serving endpoints via `llm-net` by container name.

---

## Observation

Aggregate benchmark results into reports and visualizations.

### Services

| Service | Base | Tools | Output |
| --- | --- | --- | --- |
| observation | python:3.11-slim | requests, pandas, matplotlib | observation/dashboards/ |

### Contracts

- Runs `collect_metrics.py` as entrypoint.
- Reads all `benchmark_*.json` files from `evaluation/results/` (bind-mounted).
- Produces `metrics_summary.csv` and `latency_chart.png` in `observation/dashboards/`.
- Plots avg latency over time per model.

---

## Model Management

Download and share model weights across services.

### Tools

| Tool | Language | Dependencies |
| --- | --- | --- |
| `models/download_model.py` | Python 3 | huggingface_hub |

### Contracts

- Downloads from Hugging Face Hub via `snapshot_download`.
- Auto-creates subdirectory named after model (e.g., `models/Qwen3-VL-4B-Instruct/`).
- Excludes `.msgpack`, `.h5`, `.ot` files.
- Supports `--token` for gated models.
- Models directory bind-mounted into serving and training containers.

---

## Known Implementation Gaps

These gaps need story-backed fixes before the related contracts can be marked
implemented:

- _(none currently tracked — Cross-S04 resolved the prior compose-contract
  drift items; see
  `docs/stories/epics/cross/Cross-S04-compose-contract-drift.md`.)_
