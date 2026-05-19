# E06-S01 Prometheus + Grafana Real-Time Observability

## Status

implemented

## Lane

normal

## Product Contract

Observation includes a real-time metrics stack alongside batch benchmark
reports. Prometheus scrapes local inference/runtime metrics and Grafana loads a
pre-provisioned dashboard for LLM-Local.

## Relevant Product Docs

- `docs/product/domains.md` (Observation).
- `docs/ARCHITECTURE.md` (Observability Contract).
- `README.md` (Observation usage).

## Acceptance Criteria

- `observation/docker-compose.yml` defines Prometheus and Grafana services on
  `llm-net`.
- Grafana provisions a Prometheus datasource with UID `prometheus`.
- Grafana loads `observation/grafana/dashboards/llm-local-overview.json`.
- Prometheus config scrapes vLLM `/metrics` at `vllm:8000`.
- Host ports can be overridden with `GRAFANA_HOST_PORT`,
  `PROMETHEUS_HOST_PORT`, and `GPU_EXPORTER_HOST_PORT`.
- `observation/.env.example` documents the observation environment contract;
  `observation/.env` is the local Docker Compose copy.
- GPU metrics are supported through `nvidia-gpu-exporter` behind profile `gpu`
  because it requires Linux NVIDIA device/library paths.
- Batch observation remains available through profile `batch`.

## Design Notes

- Real-time observability complements batch JSON/CSV/PNG reports; it does not
  replace benchmark artifacts.
- The core real-time stack is Prometheus + Grafana. GPU exporter is optional so
  non-NVIDIA or non-Linux hosts can still run dashboards.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python3 -m json.tool observation/grafana/dashboards/llm-local-overview.json` passes |
| Integration | `docker compose -f observation/docker-compose.yml config` resolves services and mounted config |
| E2E | Deferred until vLLM is running and Prometheus target health can be checked |
| Platform | Full GPU exporter runtime deferred to Linux NVIDIA host with `llm-net` created |
| Release | n/a |

## Harness Delta

- Added `E06-S01` to `docs/TEST_MATRIX.md`.
- Added observation story folder under `docs/stories/epics/observation/`.

## Evidence

```bash
$ python3 -m json.tool observation/grafana/dashboards/llm-local-overview.json
# exits 0

$ docker compose -f observation/docker-compose.yml config
# exits 0 and resolves prometheus, grafana, nvidia-gpu-exporter profile gpu,
# Prometheus config bind mount, Grafana provisioning, and llm-net external network.

$ cd observation && docker compose config
# exits 0 and reads defaults from observation/.env

$ docker compose -f observation/docker-compose.yml up -d prometheus grafana
network llm-net declared as external, but could not be found

$ cd observation && GRAFANA_HOST_PORT=13000 PROMETHEUS_HOST_PORT=19090 docker compose up -d prometheus grafana
# starts prometheus and grafana when default ports 3000/9090 are occupied

$ curl -fsS http://localhost:19090/-/ready
Prometheus Server is Ready.

$ curl -fsS http://localhost:13000/api/health
{
  "database": "ok",
  "version": "13.0.1+security-01",
  "commit": "9bbe672d"
}

$ curl -fsS -u admin:admin http://localhost:13000/api/datasources/name/Prometheus
# returns datasource uid "prometheus"

$ curl -fsS -u admin:admin 'http://localhost:13000/api/search?query=LLM-Local'
# returns dashboard uid "llm-local-overview"
```

Prometheus target health for `vllm` and `nvidia-gpu-exporter` remains deferred
until those services are running on `llm-net`.
