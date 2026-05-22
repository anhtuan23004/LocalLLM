# LLM-Local

Local LLM infrastructure for serving, training, evaluation, and observation.

## Directory Structure

```
├── models/              Shared model weights + download script
├── datasets/            Shared training datasets
├── serving/             Model serving services
│   ├── ollama/          Ollama (general LLM serving)
│   ├── vllm/            vLLM OpenAI-compatible serving
│   ├── sglang/          SGLang OpenAI-compatible serving
│   ├── llama.cpp/       llama.cpp OpenAI-compatible serving
│   ├── mlx/             MLX-LM host OpenAI-compatible serving
│   └── litellm/         LiteLLM gateway
├── training/            Model training/fine-tuning
│   └── unsloth/         Unsloth fine-tuning environment
├── evaluation/          Benchmark and evaluation tools
└── observation/         Metrics collection and visualization
```

## Prerequisites

Create the shared Docker network:

```bash
docker network create llm-net
```

## Usage

### Download Models

```bash
python models/download_model.py <model_id> --dir models
# Example: python models/download_model.py Qwen/Qwen3-VL-4B-Instruct --dir models
# Override or add serving targets: --target vllm --target sglang
```

Downloads the model, writes a `models/<name>/model.yaml` sidecar with
auto-detected format, size, status, and serving targets, then refreshes
`models/registry.yaml`.

### Model Registry

Each downloaded model has a `model.yaml` sidecar. The download command refreshes
the full registry automatically. If you edit sidecars by hand, rebuild the
registry with:

```bash
python models/assemble_registry.py
```

This builds `models/registry.yaml` from all sidecar files.

Default host ports avoid common service defaults:

| Service | Host port | Container/runtime port |
| --- | ---: | ---: |
| Ollama | `18134` | `11434` |
| vLLM | `18000` | `8000` |
| SGLang | `18030` | `30000` |
| llama.cpp | `18080` | `8080` |
| MLX-LM | `18081` | `18081` |
| LiteLLM | `18040` | `4000` |

Default serving targets are inferred from the downloaded format:

| Format | Default targets |
| --- | --- |
| `safetensors` / `pytorch` | `vllm`, `sglang` |
| `gguf` | `llama.cpp`, `ollama` |

Use `--target mlx` for MLX-converted models or repeat `--target` to set multiple
targets explicitly.

### Select vLLM Model

```bash
# List available vllm-targeted models
./llm-local model list

# Switch the active model
./llm-local model select GLM-OCR
```

This updates `serving/vllm/.env` with the correct model path and name.

### Start Services

```bash
# Ollama
cd serving/ollama && docker compose up -d

# vLLM (configure .env first)
cd serving/vllm && docker compose up -d

# SGLang (configure .env first)
cd serving/sglang && docker compose up -d

# llama.cpp (configure .env first, requires GGUF)
cd serving/llama.cpp && docker compose up -d

# MLX-LM on Apple Silicon (configure .env first)
serving/mlx/serve.sh

# LiteLLM gateway (configure .env first)
cd serving/litellm && docker compose up -d

# Unsloth training
cd training/unsloth && docker compose up -d
```

LiteLLM aliases are configured in `serving/litellm/config.yaml` and backed by
environment values from `serving/litellm/.env`:

| Alias | Runtime |
| --- | --- |
| `local-ollama` | Ollama |
| `local-vllm` | vLLM |
| `local-sglang` | SGLang |
| `local-llama-cpp` | llama.cpp |
| `local-mlx` | MLX-LM host server |

### Run Evaluation

```bash
cd evaluation && docker compose run --rm evaluation \
  --endpoint http://ollama:11434 \
  --model-name llama3 \
  --num-requests 20
```

Benchmark through the LiteLLM gateway:

```bash
./llm-local eval run --target litellm --model local-ollama --num-requests 20
make benchmark-litellm MODEL=local-ollama N=20
```

Quality evaluation through lm-eval-harness:

```bash
cd evaluation && docker compose --profile quality run --rm lm-eval
```

### Observation

Real-time monitoring (Prometheus + Grafana):

```bash
cd observation && docker compose up -d
```

- Grafana: `http://localhost:$GRAFANA_HOST_PORT` (admin/admin, anonymous viewing enabled)
- Prometheus: `http://localhost:$PROMETHEUS_HOST_PORT`
- Configure environment-specific ports in `observation/.env`; tracked example values live in `observation/.env.example`.

Check the active published ports with:

```bash
docker ps --format '{{.Names}} {{.Ports}}' | grep -E 'grafana|prometheus'
```

If those ports are already in use, override them:

```bash
cd observation && GRAFANA_HOST_PORT=13000 PROMETHEUS_HOST_PORT=19090 docker compose up -d
```

GPU metrics are optional and require a Linux host with NVIDIA device paths:

```bash
cd observation && docker compose --profile gpu up -d
```

Batch benchmark reports (existing):

```bash
cd observation && docker compose --profile batch run --rm observation
```

Results are saved to `evaluation/results/` and visualizations to `observation/dashboards/`.

Prometheus also scrapes LiteLLM at `litellm:4000/metrics/` when the gateway is running.
LiteLLM request and token panels populate after benchmark or client traffic is
routed through the gateway.
