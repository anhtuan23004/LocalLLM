# LiteLLM Gateway Initiative

## Status

in_progress

## Input Type

New initiative.

## Lane

normal, with stronger validation.

## Goal

Add LiteLLM as the local LLM gateway for LLM-Local so clients can use one
OpenAI-compatible endpoint while the repo keeps independent serving runtimes for
Ollama, vLLM, SGLang, llama.cpp, and MLX-LM.

LiteLLM should sit between clients and serving runtimes:

```text
clients / evaluation / Open WebUI
  -> LiteLLM proxy
    -> Ollama
    -> vLLM
    -> SGLang
    -> llama.cpp
    -> MLX-LM
```

## Why This Fits This Repo

- The repo already has several OpenAI-compatible local serving runtimes.
- `llm-net` already gives containers stable service-name routing.
- Evaluation already accepts an endpoint and model name, so it can benchmark a
  gateway without changing benchmark semantics.
- Observation already scrapes Prometheus targets, and LiteLLM can expose proxy
  metrics when configured with the Prometheus callback.

Current implementation status: E07-S01 through E07-S04 are implemented; E07-S05
Open WebUI remains planned.
- LiteLLM gives a cleaner path to request-level metrics for Ollama than the
  current `ollama-exporter`, which only exports Ollama state.

## External Contract Checked

LiteLLM official docs describe:

- Proxy Server as a central LLM gateway using OpenAI input/output format.
- `config.yaml` with `model_list` and per-model `litellm_params`.
- Docker execution with a mounted config file and `--config /app/config.yaml`.
- OpenAI clients pointing at the proxy base URL.
- Prometheus metrics exposed through `/metrics` when
  `litellm_settings.callbacks` includes `prometheus`.

## Non-Goals

- Do not remove direct runtime access. Ollama, vLLM, SGLang, llama.cpp, and
  MLX-LM remain directly reachable for debugging and runtime-specific tests.
- Do not add cloud providers in the first slice.
- Do not introduce a database, virtual-key UI, teams, budgets, or spend tracking
  in the first slice.
- Do not claim accurate Ollama latency or token metrics unless requests go
  through LiteLLM and Prometheus confirms the LiteLLM metrics.

## Proposed Topology

```text
Host
|
+-- docker network: llm-net
|   +-- litellm         (serving/litellm)      host :18040 -> container :4000
|   +-- ollama          (serving/ollama)       host :18134 -> container :11434
|   +-- vllm            (serving/vllm)         host :18000 -> container :8000
|   +-- sglang          (serving/sglang)       host :18030 -> container :30000
|   +-- llama-cpp       (serving/llama.cpp)    host :18080 -> container :8080
|   +-- prometheus      (observation/)         host $PROMETHEUS_HOST_PORT -> container :9090
|   +-- grafana         (observation/)         host $GRAFANA_HOST_PORT -> container :3000
|
+-- host-only Apple Silicon runtime
    +-- mlx-lm          (serving/mlx)          host :18081 -> host :18081
```

Default host port: `18040`, preserving the repo's `18xxx` convention for local
runtime ports while keeping LiteLLM's container port `4000`.

MLX-LM remains a host process, not a Docker service on `llm-net`; LiteLLM should
reach it through the host route when `local-mlx` is enabled.

## Proposed Files

```text
serving/litellm/
  docker-compose.yml
  config.yaml
  .env.example
  README.md

observation/prometheus/prometheus.yml
observation/grafana/dashboards/llm-local-overview.json
llm-local
Makefile
README.md
docs/product/domains.md
docs/ARCHITECTURE.md
docs/TEST_MATRIX.md
docs/stories/backlog.md
```

## Configuration Shape

First slice config should be explicit and local-only:

```yaml
model_list:
  - model_name: local-ollama
    litellm_params:
      model: os.environ/OLLAMA_LITELLM_MODEL
      api_base: os.environ/OLLAMA_API_BASE

  - model_name: local-vllm
    litellm_params:
      model: os.environ/VLLM_LITELLM_MODEL
      api_base: os.environ/VLLM_API_BASE
      api_key: os.environ/VLLM_API_KEY

  - model_name: local-sglang
    litellm_params:
      model: os.environ/SGLANG_LITELLM_MODEL
      api_base: os.environ/SGLANG_API_BASE
      api_key: os.environ/SGLANG_API_KEY

  - model_name: local-llama-cpp
    litellm_params:
      model: os.environ/LLAMA_CPP_LITELLM_MODEL
      api_base: os.environ/LLAMA_CPP_API_BASE
      api_key: os.environ/LLAMA_CPP_API_KEY

  - model_name: local-mlx
    litellm_params:
      model: os.environ/MLX_LITELLM_MODEL
      api_base: os.environ/MLX_API_BASE
      api_key: os.environ/MLX_API_KEY

litellm_settings:
  callbacks:
    - prometheus

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

Environment defaults:

```dotenv
HOST_PORT=18040
CONTAINER_PORT=4000
LITELLM_MASTER_KEY=sk-local-litellm
OLLAMA_API_BASE=http://ollama:11434
OLLAMA_LITELLM_MODEL=ollama_chat/llama3
VLLM_API_BASE=http://vllm:8000/v1
VLLM_API_KEY=sk-local-vllm
VLLM_LITELLM_MODEL=openai/Qwen/Qwen3-VL-4B-Instruct
SGLANG_API_BASE=http://sglang:30000/v1
SGLANG_API_KEY=sk-local-sglang
SGLANG_LITELLM_MODEL=openai/GLM-OCR
LLAMA_CPP_API_BASE=http://llama-cpp:8080/v1
LLAMA_CPP_API_KEY=sk-local-llama-cpp
LLAMA_CPP_LITELLM_MODEL=openai/local-gguf
MLX_API_BASE=http://host.docker.internal:18081/v1
MLX_API_KEY=sk-local-mlx
MLX_LITELLM_MODEL=openai/local-mlx
```

The exact model aliases should remain user-editable because local model names
come from the active runtime configuration, not from LiteLLM.

## Story Slices

`E07` is the LiteLLM gateway epic listed in `docs/stories/backlog.md`.
`E07-S01` through `E07-S05` are planned story slices under that epic.

### E07-S01 Minimal LiteLLM Gateway

Implemented in `docs/stories/epics/serving/E07-S01-minimal-litellm-gateway.md`.

Product contract:

- `serving/litellm/docker-compose.yml` starts a LiteLLM proxy on `llm-net`.
- The proxy exposes OpenAI-compatible `/v1/models` and
  `/v1/chat/completions` on host port `HOST_PORT`.
- First supported route: Ollama through `http://ollama:11434`.
- Config and secrets live in `.env`, with tracked examples only.

Acceptance:

- `docker compose -f serving/litellm/docker-compose.yml config` passes.
- `./llm-local serve litellm up` starts the proxy.
- `curl http://localhost:${HOST_PORT:-18040}/v1/models` works with
  `Authorization: Bearer $LITELLM_MASTER_KEY`.
- A chat completion through model alias `local-ollama` succeeds when Ollama is
  running and the configured model exists.

Evidence status: user-provided VPS runtime proof confirms
`/v1/chat/completions` succeeds through `local-ollama`.

### E07-S02 Multi-Runtime Routing

Implemented in `docs/stories/epics/serving/E07-S02-litellm-multi-runtime-routing.md`.

Product contract:

- LiteLLM has aliases for vLLM, SGLang, llama.cpp, and MLX-LM.
- Alias names are stable and backend-specific:
  - `local-ollama`
  - `local-vllm`
  - `local-sglang`
  - `local-llama-cpp`
  - `local-mlx`
- Direct runtime access remains available.

Acceptance:

- Config validates with all aliases present.
- Each alias is documented with required runtime preconditions.
- Runtime request validation for non-Ollama backends remains deferred until the
  selected backend containers are running with matching model names.

### E07-S03 Evaluation Through LiteLLM

Implemented in `docs/stories/epics/evaluation/E07-S03-litellm-evaluation-target.md`.

Product contract:

- `./llm-local eval run --target litellm --model <alias>` routes benchmark
  requests through LiteLLM.
- `make benchmark-litellm MODEL=<alias>` exists.
- Benchmark JSON records the LiteLLM alias used.

Acceptance:

- Static CLI/script validation passes; runtime benchmark JSON is deferred until
  a target backend model is running behind LiteLLM.
- Existing direct benchmark targets continue to work.

### E07-S04 LiteLLM Observability

Implemented in `docs/stories/epics/observation/E07-S04-litellm-observability.md`.

Product contract:

- Prometheus scrapes LiteLLM `/metrics/`.
- Grafana dashboard includes LiteLLM request and token panels.
- Ollama request latency is measured only for requests routed through LiteLLM.

Acceptance:

- `observation/prometheus/prometheus.yml` includes target `litellm:4000`.
- LiteLLM config enables Prometheus callback.
- LiteLLM config allows unauthenticated metrics scrapes for Prometheus.
- After a LiteLLM benchmark, Prometheus should contain LiteLLM request/tokens
  metrics.
- Grafana has panels for LiteLLM total requests, failed requests, input tokens,
  output tokens, and in-flight requests when those metrics are present.

### E07-S05 Open WebUI Adapter

Product contract:

- Open WebUI connects to LiteLLM instead of directly to each runtime.
- Open WebUI is a client of the gateway, not the source of runtime config truth.

Acceptance:

- Open WebUI service joins `llm-net`.
- Its OpenAI-compatible base URL is configured as `http://litellm:4000/v1`.
- Its local setup docs include the browser URL, login/setup steps, and the
  LiteLLM model-list smoke path.
- A local browser smoke verifies Open WebUI can load the model list through
  LiteLLM.

## Validation Ladder

| Layer | Proof |
| --- | --- |
| Unit | YAML config shape checks where possible; shell syntax for CLI/Makefile changes |
| Integration | `docker compose config`, LiteLLM `/v1/models`, LiteLLM `/metrics/`, benchmark JSON |
| E2E | `eval -> LiteLLM -> backend -> benchmark JSON -> Prometheus/Grafana` |
| Platform | Host port conflicts, `llm-net` membership, GPU policy interaction |
| Release | `./llm-local smoke` plus runtime smoke on prepared workstation |

## Risks And Decisions

- **Config drift**: LiteLLM aliases can point to models that are not loaded in a
  backend. Mitigation: document alias preconditions and consider generating
  aliases from `models/registry.yaml` later.
- **Auth confusion**: LiteLLM client auth key is separate from upstream API keys.
  Mitigation: local default `LITELLM_MASTER_KEY`, env examples, and curl docs.
- **Metrics misunderstanding**: Ollama state exporter does not measure request
  latency. Mitigation: route benchmark traffic through LiteLLM before claiming
  Ollama latency metrics in Grafana.
- **GPU contention**: LiteLLM can route to multiple GPU-heavy backends but does
  not enforce local GPU budget. Mitigation: keep Cross-S03 GPU guard as a
  prerequisite for multi-runtime workflows.
- **Provider syntax**: LiteLLM provider strings and OpenAI-compatible base URLs
  must be validated against real containers before marking stories implemented.

## Implementation Order

1. Create E07-S01 story packet and implement minimal LiteLLM -> Ollama route.
2. Add `litellm` commands to `llm-local` and Makefile.
3. Validate `local-ollama` through `/v1/chat/completions`.
4. Add `--target litellm` to evaluation.
5. Enable Prometheus callback and scrape `litellm:4000/metrics/`.
6. Add Grafana panels for LiteLLM metrics.
7. Add vLLM/SGLang/llama.cpp aliases one at a time, with runtime evidence.
8. Add Open WebUI only after the gateway path is proven.

## Exit Criteria

- LiteLLM is the documented default endpoint for client applications.
- Direct runtime endpoints remain documented for diagnostics.
- `local-ollama` plus at least one of `local-vllm` or `local-sglang` work
  through LiteLLM.
- `local-llama-cpp` and `local-mlx` remain optional runtime-specific follow-ups
  unless explicitly selected.
- Benchmarking through LiteLLM produces JSON evidence.
- LiteLLM Prometheus metrics appear after routed requests.
- Grafana clearly separates runtime-native metrics from LiteLLM gateway metrics.
