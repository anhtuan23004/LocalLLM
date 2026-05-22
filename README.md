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
├── clients/             Interactive clients
│   └── open-webui/      Open WebUI browser UI
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

### Serving Presets

Serving presets are the easiest way to switch a whole local workflow. A preset
binds the model, serving runtime, and LiteLLM alias together so clients such as
Open WebUI can keep using stable `local-*` names.

```bash
./llm-local preset list
./llm-local preset show chat-small
./llm-local preset apply chat-small --dry-run --render
./llm-local preset apply chat-small
./llm-local preset active
./llm-local config render
```

Use `--pull` when the preset uses an Ollama model that still needs to be pulled,
`--render` when you want to update runtime `.env` files immediately, and
`--restart` when you want the affected runtime and LiteLLM restarted after
rendering:

```bash
./llm-local preset apply chat-small --pull --render --restart
```

`profile` is reserved for Docker Compose profiles such as `gpu`, `batch`, and
`quality`; model workflow bindings are called serving presets.

Applied presets are stored as generated local state in `config/active/serving.yaml`
(gitignored). Runtime `.env` files remain local machine configuration; `config
render` translates the active preset into the small set of runtime model env
values that Docker Compose needs.

Default host ports avoid common service defaults:

| Service | Host port | Container/runtime port |
| --- | ---: | ---: |
| Ollama | `18134` | `11434` |
| vLLM | `18000` | `8000` |
| SGLang | `18030` | `30000` |
| llama.cpp | `18080` | `8080` |
| MLX-LM | `18081` | `18081` |
| LiteLLM | `18040` | `4000` |
| Open WebUI | `18088` | `8080` |

Default serving targets are inferred from the downloaded format:

| Format | Default targets |
| --- | --- |
| `safetensors` / `pytorch` | `vllm`, `sglang` |
| `gguf` | `llama.cpp`, `ollama` |

Use `--target mlx` for MLX-converted models or repeat `--target` to set multiple
targets explicitly.

### Select Runtime Model

```bash
# List available models
./llm-local model list

# Power-user path: switch one runtime directly
./llm-local model select GLM-OCR --runtime vllm --restart
```

This updates the selected runtime `.env` with the correct model path and name.
For normal workflow switching, prefer `./llm-local preset apply <id>`.

### Start Services

```bash
# Optional: inspect startup guardrails before changing services
./llm-local guardrails --all

# Ollama
./llm-local serve ollama up

# vLLM (configure .env first)
./llm-local serve vllm up

# SGLang (configure .env first)
./llm-local serve sglang up

# llama.cpp (configure .env first, requires GGUF)
./llm-local serve llama.cpp up

# MLX-LM on Apple Silicon (configure .env first)
./llm-local serve mlx up

# LiteLLM gateway (configure .env first)
./llm-local serve litellm up

# Open WebUI browser client (configure .env first)
./llm-local webui up

# Unsloth training
./llm-local train up
```

`llm-local` runs startup guardrails before `serve ... up`, `webui up`, and
`train up`. The guardrails check host port conflicts, running service health,
model/runtime compatibility for configured local model paths, and the GPU budget
rules from `docs/decisions/0005-gpu-budget-allocation.md`.
On known-good remote Docker hosts where `nvidia-smi` is unavailable locally, set
`LLM_LOCAL_SKIP_GPU_CHECK=1` to bypass only the local GPU probe.

LiteLLM aliases are configured in `serving/litellm/config.yaml` and backed by
environment values from `serving/litellm/.env`:

| Alias | Runtime |
| --- | --- |
| `local-ollama` | Ollama |
| `local-vllm` | vLLM |
| `local-sglang` | SGLang |
| `local-llama-cpp` | llama.cpp |
| `local-mlx` | MLX-LM host server |

### Interactive UI

Open WebUI is configured as a client of LiteLLM:

```bash
./llm-local serve litellm up
./llm-local webui up
```

Open `http://localhost:18088`, create the first local admin account, and select
a LiteLLM alias such as `local-ollama`.

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

For the Phase 2 end-to-end Ollama workflow, use
`docs/runbooks/ollama-golden-path.md`.

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
