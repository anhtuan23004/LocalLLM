# E07-S04 LiteLLM Observability

## Status

implemented

## Lane

normal

## Product Contract

Prometheus scrapes LiteLLM gateway metrics and Grafana separates gateway-level
request/token behavior from runtime-native metrics.

## Relevant Product Docs

- `docs/product/domains.md` (Observation).
- `docs/ARCHITECTURE.md` (Observability Contract).
- `docs/stories/initiatives/litellm-gateway.md`.
- `serving/litellm/README.md`.

## Acceptance Criteria

- `serving/litellm/config.yaml` enables the LiteLLM Prometheus callback and
  allows unauthenticated metrics scrapes.
- `observation/prometheus/prometheus.yml` scrapes `litellm:4000/metrics/`.
- Grafana dashboard includes LiteLLM panels for total requests, failed
  requests, input tokens, output tokens, and in-flight requests when that metric
  is present.
- Ollama latency/token panels are not claimed from `ollama-exporter`; request
  metrics for Ollama require traffic routed through LiteLLM.

## Design Notes

- LiteLLM request/token metrics are generated after gateway traffic, so the
  dashboard panels may be empty before the first benchmark or client request.
- The dashboard uses LiteLLM documented metric names and also accepts common
  Prometheus counter `_total` suffix variants.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | JSON parse for `llm-local-overview.json`; YAML parse for Prometheus config |
| Integration | `docker compose -f observation/docker-compose.yml config`; `/metrics/` from a running LiteLLM gateway |
| E2E | Prometheus query after a LiteLLM benchmark deferred until a backend model is available |
| Platform | n/a |
| Release | `./llm-local smoke` includes dashboard JSON validation |

## Harness Delta

- Added this story packet.
- Added `E07-S04` to `docs/TEST_MATRIX.md`.
- Updated the LiteLLM initiative and story backlog link.

## Evidence

```bash
$ python3 -m json.tool observation/grafana/dashboards/llm-local-overview.json
# exits 0

$ python3 - <<'PY'
import pathlib
import yaml
for path in [
    pathlib.Path('serving/litellm/config.yaml'),
    pathlib.Path('observation/prometheus/prometheus.yml'),
]:
    with path.open() as f:
        yaml.safe_load(f)
    print(f'{path}: ok')
PY
# exits 0

$ docker compose -f observation/docker-compose.yml config
# exits 0 and resolves the Prometheus config mount and Grafana dashboard mount.

$ ./llm-local serve litellm up
# starts the LiteLLM gateway

$ curl -fsS http://localhost:18040/metrics/ | rg 'litellm_proxy_total_requests_metric_total|litellm_input_tokens_metric_total|litellm_output_tokens_metric_total|litellm_in_flight_requests'
# exits 0 and confirms LiteLLM gateway metric families are exposed.

$ ./llm-local observe up
# starts Prometheus and Grafana using observation/.env ports.

$ curl -fsS 'http://localhost:9092/api/v1/query?query=up%7Bjob%3D%22litellm%22%7D'
# returns up{job="litellm",instance="litellm:4000"} = 1

$ curl -fsS 'http://localhost:9092/api/v1/targets?state=active'
# includes scrapeUrl "http://litellm:4000/metrics/" with health "up".

$ prometheus query: litellm_requests_metric_created
# user-provided VPS proof returned one LiteLLM request series for
# api_provider="ollama_chat", model="qwen2.5:0.5b",
# instance="litellm:4000", job="litellm", user_agent="curl/7.68.0".

$ ./llm-local observe down && ./llm-local serve litellm down
# stops and removes the temporary containers.
```

Prometheus request/token metric proof remains deferred until a benchmark or
client request can complete through LiteLLM to a running backend model.
