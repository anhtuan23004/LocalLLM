# Architecture

## Discovery Answers (LLM-Local)

- **Product surfaces**: CLI (`llm-local`, Makefile), REST APIs (Ollama, vLLM, SGLang, llama.cpp, MLX-LM OpenAI-compat, LiteLLM gateway), Jupyter Lab (training), Grafana/Prometheus (observation).
- **Runtime stack**: Docker Compose, Python 3.11, NVIDIA CUDA GPU, vLLM, SGLang, llama.cpp, Ollama, LiteLLM, Unsloth, Prometheus, Grafana, and host-side MLX-LM on Apple Silicon.
- **Core domains**: Serving, Training, Evaluation, Observation, Model Management.
- **Boundary inputs**: CLI arguments (benchmark params, model download args), environment variables (.env files), HTTP API requests (OpenAI-compat), filesystem (model weights, benchmark JSON, CSV/PNG output).
- **Validation ladder**: Docker healthchecks → benchmark JSON schema → metrics CSV + chart generation → cross-service network reachability.

Stack choices recorded in `docs/decisions/0004-docker-compose-shared-network.md`.

## Topology

```text
Host (NVIDIA GPU workstation)
│
├── docker network: llm-net (external, bridge)
│   ├── ollama          (serving/ollama)       host :18134 → container :11434
│   ├── vllm            (serving/vllm)         host :18000 → container :8000
│   ├── sglang          (serving/sglang)       host :18030 → container :30000
│   ├── llama-cpp       (serving/llama.cpp)    host :18080 → container :8080
│   ├── litellm         (serving/litellm)      host :18040 → container :4000
│   ├── unsloth         (training/unsloth)     :8888, :8001, :2222
│   ├── evaluation      (evaluation/)          run-once
│   ├── observation     (observation/)         run-once (batch profile)
│   ├── prometheus      (observation/)         host $PROMETHEUS_HOST_PORT → container :9090
│   ├── grafana         (observation/)         host $GRAFANA_HOST_PORT → container :3000
│   └── nvidia-gpu-exporter (observation/)     :9835
│
├── Bind mounts:
│   ├── models/         → serving (vllm, sglang, llama.cpp), training (unsloth)
│   ├── datasets/       → training (unsloth)
│   ├── evaluation/results/ → evaluation, observation
│   └── observation/dashboards/ → observation
│
└── Docker volumes:
    └── ollama_data     → ollama (/root/.ollama)

Host-only Apple Silicon path:
└── mlx_lm.server       (serving/mlx)          :18081
```

## Default Layering (adapted)

The generic DDD layering from the harness template does not apply directly.
LLM-Local is infrastructure-as-code, not a domain application. The relevant
layers are:

```text
Configuration (.env, docker-compose.yml)
  <- Services (Docker containers)
    <- Scripts (Python CLI tools)
      <- Shared Resources (models/, datasets/, results/)
```

## Dependency Rule (adapted)

| Layer | May depend on | Must not depend on |
| --- | --- | --- |
| Scripts | Shared resources, service APIs | Docker internals, other scripts |
| Services | Shared resources (bind mounts), llm-net | Other services being up (no hard deps) |
| Configuration | Nothing | Hardcoded paths (use env vars) |

## Parse-First Boundary Rule (adapted)

- `.env` files parsed by Docker Compose before container start.
- CLI arguments parsed by argparse in Python scripts.
- Benchmark results validated as JSON before observation consumes them.
- Model paths validated by download script before writing.

## Observability Contract (adapted)

**Real-time** (always-on core, optional GPU profile):

- Prometheus scrapes vLLM, SGLang, llama.cpp, LiteLLM, Ollama state through
  `ollama-exporter`, and, when `--profile gpu` is enabled, nvidia-gpu-exporter
  every 15s.
- Grafana dashboard: GPU utilization, VRAM, temperature, vLLM p95 latency,
  tokens/s, queue depth, Ollama availability/model state, and LiteLLM gateway
  request totals, failed request totals, token totals, and in-flight requests
  when present. The current dashboard does not include SGLang runtime-specific
  panels.
- Default host ports are Grafana `3000` and Prometheus `9090`; `observation/.env` can override them with `GRAFANA_HOST_PORT` and `PROMETHEUS_HOST_PORT`.

**Batch** (on-demand via `--profile batch`):

- Benchmark JSON per run (timestamp, latency stats, per-request details).
- Aggregated CSV summary across runs.
- Latency-over-time chart (PNG).
