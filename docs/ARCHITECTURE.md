# Architecture

## Discovery Answers (LLM-Local)

- **Product surfaces**: CLI (docker compose commands), REST APIs (Ollama, vLLM OpenAI-compat), Jupyter Lab (training).
- **Runtime stack**: Docker Compose, Python 3.11, NVIDIA CUDA GPU, vLLM, Ollama, Unsloth.
- **Core domains**: Serving, Training, Evaluation, Observation, Model Management.
- **Boundary inputs**: CLI arguments (benchmark params, model download args), environment variables (.env files), HTTP API requests (OpenAI-compat), filesystem (model weights, benchmark JSON, CSV/PNG output).
- **Validation ladder**: Docker healthchecks → benchmark JSON schema → metrics CSV + chart generation → cross-service network reachability.

Stack choices recorded in `docs/decisions/0004-docker-compose-shared-network.md`.

## Topology

```text
Host (NVIDIA GPU workstation)
│
├── docker network: llm-net (external, bridge)
│   ├── ollama          (serving/ollama)       :11434
│   ├── vllm            (serving/vllm)         :8000
│   ├── unsloth         (training/unsloth)     :8888, :8001, :2222
│   ├── evaluation      (evaluation/)          run-once
│   └── observation     (observation/)         run-once
│
├── Bind mounts:
│   ├── models/         → serving (vllm), training (unsloth)
│   ├── datasets/       → training (unsloth)
│   ├── evaluation/results/ → evaluation, observation
│   └── observation/dashboards/ → observation
│
└── Docker volumes:
    └── ollama_data     → ollama (/root/.ollama)
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

Current observability is batch-oriented:

- Benchmark JSON per run (timestamp, latency stats, per-request details).
- Aggregated CSV summary across runs.
- Latency-over-time chart (PNG).

Future consideration: real-time metrics via Prometheus + Grafana.
