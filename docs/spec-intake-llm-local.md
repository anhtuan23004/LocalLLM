# Spec Intake — LLM-Local

Date: 2026-05-18

## Source

- Existing repository code and README.md
- Docker-compose configurations across serving/, training/, evaluation/, observation/
- Model download script in models/

## Project Summary

LLM-Local is a local LLM infrastructure platform for serving, training,
evaluation, and observation of large language models. It targets developers and
ML engineers who want to run, fine-tune, benchmark, and monitor LLMs on local
GPU hardware without cloud dependencies.

The platform uses Docker Compose with a shared `llm-net` network so all
services can communicate. Each domain (serving, training, evaluation,
observation) is an independent compose stack that joins the shared network.

## Candidate Product Docs

| File | Purpose | Source sections |
| --- | --- | --- |
| `docs/product/overview.md` | Platform vision, users, and domain map | README.md |
| `docs/product/domains.md` | Contracts for each domain: serving, training, evaluation, observation | All docker-compose files |

## Candidate Epics

| Epic | Description | Status |
| --- | --- | --- |
| E01-serving | Model serving via Ollama and vLLM (Qwen-VL) | unsliced |
| E02-training | Fine-tuning with Unsloth (Jupyter + GPU) | unsliced |
| E03-evaluation | Latency benchmarking against serving endpoints | unsliced |
| E04-observation | Metrics collection and visualization from benchmark results | unsliced |
| E05-model-management | Model download, storage, and sharing across services | unsliced |

## Architecture Questions

- Runtime stack: Docker Compose, Python 3.11, NVIDIA GPU (CUDA)
- Product surfaces: CLI (docker compose commands), Jupyter (training), REST APIs (serving)
- Storage: Local filesystem (models/, datasets/, evaluation/results/, observation/dashboards/), Docker volumes (ollama_data)
- External providers: Hugging Face Hub (model downloads), Docker Hub (base images)
- Deployment target: Local workstation with NVIDIA GPU(s)
- Security model: Local-only; no auth on serving endpoints; Jupyter password on training

## Validation Shape

| Layer | Expected proof |
| --- | --- |
| Unit | Python scripts (download_model, run_benchmark, collect_metrics) |
| Integration | Docker compose up + healthcheck pass for each service |
| E2E | Full pipeline: serve model → run benchmark → collect metrics → generate chart |
| Platform | GPU passthrough works; shared network connectivity between containers |
| Release | All services start cleanly; benchmark produces valid JSON; observation produces chart |

## Open Decisions

- Whether to add a top-level docker-compose.yml that orchestrates all services together.
- Whether to add Prometheus/Grafana for real-time observation vs current batch approach.
- Whether evaluation should support lm-eval-harness tasks beyond latency benchmarks.
- Whether to add model registry/versioning beyond flat filesystem.

## First Story Candidates

- Validate all services start and pass healthchecks on shared network.
- Add top-level orchestration compose file.
- Add GPU availability pre-check script.
- Expand evaluation to support lm-eval-harness task suites.
- Add model inventory command (list downloaded models with sizes).

## Harness Delta

- Created this spec-intake document.
- Created product docs (`overview.md`, `domains.md`).
- Updated story backlog with candidate epics.
- Created architecture decision for Docker Compose with shared network.
- Updated `docs/TEST_MATRIX.md` with initial rows.
- Updated `docs/ARCHITECTURE.md` with LLM-Local discovery answers.
