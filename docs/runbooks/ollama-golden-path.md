# Ollama Golden Path

This is the Phase 2 golden path: one small model, one serving runtime, one
benchmark, one batch observation report, and optional real-time metrics.

Use this path before expanding to vLLM, SGLang, llama.cpp, MLX-LM, or Open
WebUI.

## Scope

Runtime: Ollama.

Small model: `qwen2.5:0.5b`.

Gateway alias, when using LiteLLM: `local-ollama`.

## Preconditions

- Docker and Docker Compose are installed.
- The repo virtualenv or Python dependencies are available.
- Ports are not conflicting:
  - Ollama host port: `18134`.
  - LiteLLM host port: `18040`.
  - Grafana and Prometheus use `observation/.env` when present; check with:

```bash
cat observation/.env 2>/dev/null || cat observation/.env.example
```

## 1. Start Ollama

```bash
./llm-local serve ollama up
```

Expected:

```text
Container ollama Started
```

Verify:

```bash
curl -fsS http://localhost:18134/api/tags
```

Expected: JSON with a `models` array. It may be empty before the first pull.

## 2. Download A Small Model

```bash
docker exec ollama ollama pull qwen2.5:0.5b
```

Expected:

```text
pulling manifest
pulling ...
verifying sha256 digest
success
```

Verify:

```bash
docker exec ollama ollama list | grep qwen2.5
```

Expected: a row for `qwen2.5:0.5b`.

## 3. Select The Model

For direct Ollama requests, selection is the request model name:

```text
qwen2.5:0.5b
```

For LiteLLM gateway requests, set the Ollama upstream model in
`serving/litellm/.env`:

```dotenv
OLLAMA_API_BASE=http://ollama:11434
OLLAMA_LITELLM_MODEL=ollama_chat/qwen2.5:0.5b
```

Then start LiteLLM:

```bash
./llm-local serve litellm up
```

Verify model list:

```bash
curl -fsS -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-local-litellm}" \
  http://localhost:18040/v1/models
```

Expected: `local-ollama` appears in the returned model list.

## 4. Run A Chat Smoke

Direct Ollama:

```bash
curl -fsS -X POST http://localhost:18134/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:0.5b",
    "messages": [{"role": "user", "content": "Xin chao, tra loi ngan gon."}]
  }'
```

LiteLLM gateway:

```bash
curl -fsS -X POST http://localhost:18040/v1/chat/completions \
  -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-local-litellm}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-ollama",
    "messages": [{"role": "user", "content": "Xin chao, tra loi ngan gon."}]
  }'
```

Expected: OpenAI-compatible JSON with:

```text
"object":"chat.completion"
"choices":[...]
"usage":{"completion_tokens":...,"prompt_tokens":...,"total_tokens":...}
```

## 5. Run Benchmark

Direct Ollama:

```bash
./llm-local eval run \
  --target ollama \
  --model qwen2.5:0.5b \
  --num-requests 3 \
  --prompt "Xin chao, tra loi ngan gon."
```

LiteLLM gateway:

```bash
./llm-local eval run \
  --target litellm \
  --model local-ollama \
  --num-requests 3 \
  --prompt "Xin chao, tra loi ngan gon."
```

Expected:

```text
[1/3] status=200 latency=...
[2/3] status=200 latency=...
[3/3] status=200 latency=...
Results saved to /app/results/benchmark_...json
Avg latency: ...
```

Host artifact:

```bash
ls -lt evaluation/results/benchmark_*.json | head
```

Expected: newest benchmark JSON exists.

## 6. Run Batch Observation

```bash
./llm-local observe batch
```

Expected:

```text
Summary saved to /app/dashboards/metrics_summary.csv
Chart saved to /app/dashboards/latency_chart.png
```

Host artifacts:

```bash
ls -l observation/dashboards/metrics_summary.csv \
      observation/dashboards/latency_chart.png
```

Expected: both files exist and have recent timestamps.

## 7. View Prometheus And Grafana

Start real-time observation:

```bash
./llm-local observe up
```

Find published ports:

```bash
docker ps --format '{{.Names}} {{.Ports}}' | grep -E 'grafana|prometheus'
```

Default or local URLs:

- Grafana: `http://localhost:3000` or `http://localhost:3003` when
  `observation/.env` overrides `GRAFANA_HOST_PORT`.
- Prometheus: `http://localhost:9090` or `http://localhost:9092` when
  `observation/.env` overrides `PROMETHEUS_HOST_PORT`.

Useful Prometheus checks:

```text
up{job="ollama"}
ollama_up
up{job="litellm"}
litellm_proxy_total_requests_metric_total
litellm_requests_metric_total
litellm_requests_metric_created
litellm_input_tokens_metric_total
litellm_output_tokens_metric_total
```

Expected:

- `up{job="ollama"}` is `1` when `ollama-exporter` is running.
- `ollama_up` is `1` when Ollama is reachable from the exporter.
- `up{job="litellm"}` is `1` when LiteLLM is running.
- LiteLLM request/token metrics appear after traffic goes through LiteLLM.
- `litellm_requests_metric_created` is metadata for the LiteLLM request metric
  family. Use `litellm_requests_metric_total` or
  `litellm_proxy_total_requests_metric_total` for request counts.

Grafana:

- Open the `LLM-Local Overview` dashboard.
- Ollama panels show availability/model state.
- LiteLLM panels show request/token counters after gateway traffic.

## Common Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `network llm-net declared as external, but could not be found` | Compose was run directly before network creation | `docker network create llm-net` or use `./llm-local serve ...` |
| `curl: (7) Failed to connect` | Service is not running or wrong host port | `docker ps --format '{{.Names}} {{.Ports}}'` |
| `model not found` from Ollama | Model was not pulled | `docker exec ollama ollama pull qwen2.5:0.5b` |
| LiteLLM returns `401` | Missing or wrong bearer token | Add `Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-local-litellm}` |
| LiteLLM returns upstream/model error | `OLLAMA_LITELLM_MODEL` does not match pulled model | Set `OLLAMA_LITELLM_MODEL=ollama_chat/qwen2.5:0.5b` and restart LiteLLM |
| Benchmark has `status=404` | Benchmark model name does not match target | Use `qwen2.5:0.5b` for `--target ollama`; use `local-ollama` for `--target litellm` |
| Batch observation creates no useful report | No benchmark JSON exists | Run benchmark first and check `evaluation/results/` |
| Prometheus target down for vLLM/SGLang/llama.cpp | Those runtimes are not part of this golden path | Ignore unless validating those runtimes |
| Grafana/Prometheus not on `3000`/`9090` | Local `.env` overrides ports | Use `docker ps` or read `observation/.env` |

## Evidence To Capture

When this path is validated on a workstation or VPS, paste these into the
relevant story evidence:

```text
docker exec ollama ollama list | grep qwen2.5
curl direct Ollama chat completion output
curl LiteLLM chat completion output, if gateway path was used
benchmark command output showing status=200
ls -l evaluation/results/benchmark_*.json
./llm-local observe batch output
ls -l observation/dashboards/metrics_summary.csv observation/dashboards/latency_chart.png
Prometheus query result for ollama_up and, if used, up{job="litellm"}
```
