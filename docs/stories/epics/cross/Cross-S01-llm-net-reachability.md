# Cross-S01 llm-net Service Reachability

## Status

implemented

## Lane

normal

## Product Contract

Containers attached to the shared external `llm-net` network can resolve and
reach the local LLM services by compose service name.

## Relevant Product Docs

- `docs/ARCHITECTURE.md` (Topology).
- `docs/product/domains.md` (Serving, Evaluation, Training, Observation).
- `docs/decisions/0004-docker-compose-shared-network.md`.

## Acceptance Criteria

- `llm-net` exists on the Docker host.
- Evaluation container can reach Ollama by service name at
  `http://ollama:11434`.
- Evaluation container can reach vLLM by service name at
  `http://vllm:8000` when vLLM is running.
- Training container can use `OLLAMA_HOST=http://ollama:11434`.
- Failures are service-state failures, not DNS/network topology failures.

## Design Notes

- This proves the shared-network contract, not the model quality or latency.
- The evaluation container is the preferred probe because it is run-once and
  already depends on serving endpoints.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | n/a |
| Integration | Service-name HTTP checks from evaluation container succeed |
| E2E | n/a |
| Platform | Docker external network exists on target host |
| Release | n/a |

## Harness Delta

- Added this story packet and updated `docs/TEST_MATRIX.md`.

## Evidence

```bash
$ docker network inspect llm-net
# exits 0

$ cd evaluation
$ docker compose run --rm --entrypoint python evaluation - <<'PY'
import requests

checks = {
    "ollama": "http://ollama:11434/api/tags",
    "vllm": "http://vllm:8000/health",
}

for name, url in checks.items():
    response = requests.get(url, timeout=10)
    print(name, response.status_code)
    response.raise_for_status()
PY
ollama 200
vllm 200
```

The training compose configuration also resolves `OLLAMA_HOST` to the shared
network service name:

```bash
$ docker compose -f training/unsloth/docker-compose.yml config | grep -A1 OLLAMA_HOST
      OLLAMA_HOST: http://ollama:11434
```
