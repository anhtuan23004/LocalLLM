# Product Domains — LLM-Local

## Serving

Expose LLM inference endpoints on the local network.

### Services

| Service | Engine | API | Host port | Runtime port | GPU |
| --- | --- | --- | ---: | ---: | --- |
| Ollama | ollama/ollama:0.24.0 | Ollama API + OpenAI-compat | 18134 | 11434 | all |
| vLLM | vllm/vllm-openai | OpenAI-compatible | 18000 | 8000 | GPU 0 by default |
| SGLang | lmsysorg/sglang:v0.5.12.post1 | OpenAI-compatible | 18030 | 30000 | GPU 0 by default |
| llama.cpp | ghcr.io/ggml-org/llama.cpp:server-cuda@sha256:213012cb085f3f9042179915b987e9d28617a91f3b4a6e37991ab7dbb0de1bf1 | OpenAI-compatible | 18080 | 8080 | GPU 0 by default |
| MLX-LM | mlx-lm host process | OpenAI-compatible | 18081 | 18081 | Apple Silicon Metal |
| LiteLLM | docker.litellm.ai/berriai/litellm:v1.72.6-stable | OpenAI-compatible gateway | 18040 | 4000 | none |
| Open WebUI | ghcr.io/open-webui/open-webui:v0.6.15 | Browser UI client | 18088 | 8080 | none |
| OCR Extract | llm-local-ocr-extract:0.1.0 | Gemini-OCR-like public OCR API v1 | 18092 | 8092 | none |

### Contracts

- Ollama exposes `/api/generate`, `/api/chat`, and OpenAI-compatible `/v1/chat/completions`.
- vLLM exposes `/v1/chat/completions` and `/health`.
- SGLang exposes `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, `/health`, and `/metrics`.
- llama.cpp exposes OpenAI-compatible `/v1/chat/completions` and `/v1/embeddings` for GGUF models.
- MLX-LM exposes OpenAI-compatible chat completions from a host Apple Silicon process.
- LiteLLM exposes OpenAI-compatible `/v1/models` and `/v1/chat/completions`
  as a gateway to local runtimes. Stable aliases are `local-ollama`,
  `local-vllm`, `local-sglang`, `local-llama-cpp`, and `local-mlx`.
- Open WebUI exposes a browser interface for interactive use and connects to
  LiteLLM as its OpenAI-compatible provider at `http://litellm:4000/v1`.
- OCR Extract exposes `POST /api/v1/ocr/classify-segment` and
  `POST /api/v1/ocr/extract` for schema-driven document classification and
  extraction. It accepts image or PDF `file_url`, renders PDF pages to images
  internally, rejects private/reserved `file_url` destinations before and after
  redirects, requires strict structured model output, and calls LiteLLM through
  the configured `LITELLM_MODEL` Gateway Alias.
- Docker services join `llm-net` and are reachable by container name from other services.
- Healthchecks defined: Ollama via `ollama list`, vLLM via curl `/health`, SGLang via curl `/health`.

### Configuration

- Runtime facts shared by the CLI, guardrails, validation, and model preset
  rendering are centralized in `config/runtime-catalog.yaml`.
- Tracked image defaults are pinned in the runtime catalog and compose defaults;
  local `.env` files may override them deliberately.
- Ollama: stateless config, model data in `ollama_data` Docker volume.
- vLLM: `.env` file controls model path, served model name, GPU allocation, memory utilization, and tensor parallelism.
- SGLang: `.env` file controls model path, host/container ports, tensor parallelism, memory fraction, and GPU allocation.
- llama.cpp: `.env` file controls GGUF model path, host/container ports, context size, parallel slots, and GPU layer offload.
- MLX-LM: `.env` file controls host model id/path and port; it runs outside Docker on Apple Silicon.
- LiteLLM: `.env` file controls host/container ports, proxy master key,
  upstream API base URLs, upstream API keys for OpenAI-compatible runtimes, and
  the model strings exposed behind the `local-*` aliases.
- Open WebUI: `.env` file controls host/container ports, UI auth settings,
  persistent secret key, and the LiteLLM OpenAI-compatible base URL/key. Direct
  Ollama API integration is disabled by default so LiteLLM remains the client
  gateway.
- OCR Extract: `.env` file controls host/container ports, LiteLLM base URL,
  LiteLLM API key, required `LITELLM_MODEL`, request timeout, maximum file size,
  maximum PDF page count, and PDF render DPI. Public requests do not accept
  model/provider override fields; switching model behavior happens through the
  Gateway Alias.
- Host ports use the `18xxx` range by default to avoid common local service conflicts while keeping runtime/container ports unchanged.

---

## Training

Fine-tune models using GPU-accelerated Jupyter environment.

### Services

| Service | Engine | Interface | Port | GPU |
| --- | --- | --- | --- | --- |
| Unsloth | unsloth/unsloth:2026.5.7-pt2.10.0-vllm-0.16.0-cu12.8-studio-release-v0.1.41-beta-2026-MAY-24 | Jupyter Lab | 8888 | all |

### Contracts

- Jupyter accessible at `localhost:8888` with password auth.
- SSH available on port 2222.
- Secondary API port on 8001 (maps to container 8000).
- Mounts `models/` and `datasets/` from repo root for shared access.
- Work directory persisted at `training/unsloth/work/`.
- Can reach Ollama at `http://ollama:11434` via `llm-net`.

---

## Evaluation

Benchmark model serving endpoints for latency and quality.

### Services

| Service | Base | Tools | Output |
| --- | --- | --- | --- |
| evaluation | python:3.11-slim | requests, pandas, lm-eval | evaluation/results/*.json |
| lm-eval | python:3.11-slim | lm-eval-harness OpenAI-compatible API backend | evaluation/results/lm-eval/ |

### Contracts

- Runs `run_benchmark.py` as entrypoint with CLI args: `--endpoint`, `--model-name`, `--num-requests`, `--prompt`, and optional `--api-key`.
- Sends N chat completion requests, records per-request latency.
- Outputs JSON with summary stats (avg/min/max latency, success count).
- `./llm-local eval run --target litellm --model <alias>` routes benchmark
  traffic through the LiteLLM gateway and passes the local gateway bearer token.
- Runs `lm_eval` through `run_lm_eval.sh` for quality evaluation against OpenAI-compatible serving endpoints.
- Uses `local-chat-completions` by default with `--apply_chat_template`, `--batch_size 1`, and env-configured model/task/endpoint values.
- Defaults to a small smoke run (`LM_EVAL_TASKS=gsm8k`, `LM_EVAL_LIMIT=10`) so local validation is bounded on a 12GB VRAM target.
- Results saved to `evaluation/results/` (bind-mounted).
- Reaches serving endpoints via `llm-net` by container name.

---

## Observation

Aggregate benchmark results into reports and visualizations, and expose
real-time runtime dashboards for inference and GPU metrics.

### Services

| Service | Base | Tools | Output |
| --- | --- | --- | --- |
| observation | python:3.11-slim | requests, pandas, matplotlib | observation/dashboards/ |
| prometheus | prom/prometheus | Prometheus | metrics store + scrape targets |
| grafana | grafana/grafana | Grafana | provisioned datasource + dashboard |
| ollama-exporter | python:3.11-slim | Ollama API poller | Prometheus metrics for Ollama state |
| nvidia-gpu-exporter | utkuozdemir/nvidia_gpu_exporter | nvidia-smi exporter | GPU metrics on profile `gpu` |

### Contracts

- Prometheus scrapes vLLM `/metrics` at `vllm:8000`, SGLang `/metrics` at `sglang:30000`, llama.cpp `/metrics` at `llama-cpp:8080`, Ollama state metrics through `ollama-exporter:9101`, LiteLLM gateway metrics at `litellm:4000/metrics/`, and the optional GPU exporter at `nvidia-gpu-exporter:9835`.
- Grafana provisions the Prometheus datasource with UID `prometheus`.
- Grafana loads `llm-local-overview.json` with panels for GPU utilization,
  VRAM, temperature, vLLM latency, token throughput, request queue depth,
  Ollama availability/model state, and LiteLLM gateway request totals, failed
  request totals, token totals, and in-flight requests when present. The
  current dashboard does not include SGLang runtime-specific panels.
- Host ports default to Grafana `3000`, Prometheus `9090`, and GPU exporter `9835`; environments can override them with `GRAFANA_HOST_PORT`, `PROMETHEUS_HOST_PORT`, and `GPU_EXPORTER_HOST_PORT` in `observation/.env`.
- GPU exporter is opt-in via `docker compose --profile gpu up -d` because it depends on Linux NVIDIA device/library paths.
- Runs `collect_metrics.py` as entrypoint.
- Reads all `benchmark_*.json` files from `evaluation/results/` (bind-mounted).
- Produces `metrics_summary.csv` and `latency_chart.png` in `observation/dashboards/`.
- Plots avg latency over time per model.

---

## Model Management

Download, inventory, and convert model weights across services.

### Tools

| Tool | Language | Dependencies |
| --- | --- | --- |
| `models/download_model.py` | Python 3 | huggingface_hub, ruamel.yaml |
| `models/registry.yaml` | YAML | — |
| `models/assemble_registry.py` | Python 3 | ruamel.yaml |
| `models/convert.sh` | Bash | git, llama.cpp, optional `convert` Python extra, ollama CLI |
| `models/presets.yaml` | YAML | — |
| `models/presets.py` | Python 3 | ruamel.yaml |
| `models/validate_registry.py` | Python 3 | ruamel.yaml |

### Contracts

- Downloads from Hugging Face Hub via `snapshot_download`.
- Auto-creates subdirectory named after model (e.g., `models/Qwen3-VL-4B-Instruct/`).
- Excludes `.msgpack`, `.h5`, `.ot` files.
- Supports `--token` for gated models.
- Writes `models/<name>/model.yaml` sidecars and refreshes `registry.yaml` after successful downloads.
- `registry.yaml` tracks all models: id, repo, format, size_gb, path, serving_target, serving_targets, quantizations, downloaded.
- Default serving targets are inferred by format: safetensors/PyTorch targets vLLM and SGLang; GGUF targets llama.cpp and Ollama; MLX can be set explicitly with `--target mlx`.
- Serving presets in `models/presets.yaml` bind a model, serving runtime, and
  LiteLLM gateway alias for workflow-level switching.
- `./llm-local preset apply <id>` writes generated local active state to
  `config/active/serving.yaml`.
- `./llm-local config render` updates runtime model `.env` values from the
  active preset, including the matching LiteLLM model env var.
- `./llm-local model select <id> --runtime <runtime>` remains the lower-level
  power-user command for runtime-specific model selection.
- `convert.sh hf2gguf <path>` converts HuggingFace weights to GGUF via llama.cpp `convert_hf_to_gguf.py`; llama.cpp is shallow-cloned into `vendor/llama.cpp` on first use.
- `convert.sh gguf2ollama <path>` imports GGUF into Ollama via `ollama create` with generated Modelfile.
- `validate_registry.py --metadata-only` checks registry metadata for quick
  validation without requiring ignored local model weights. Strict
  `validate_registry.py` also checks local paths and expected model files.
- Models directory bind-mounted into serving and training containers.

---

## Known Implementation Gaps

These gaps need story-backed fixes before the related contracts can be marked
implemented:

- vLLM runtime proof remains planned. E01-S02 must record healthcheck and
  OpenAI-compatible chat-completion evidence on a prepared CUDA host before the
  vLLM serving contract can be marked implemented.
