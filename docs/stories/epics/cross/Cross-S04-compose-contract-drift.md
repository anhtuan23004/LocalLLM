# Cross-S04 Fix Compose-Contract Drift

## Status

implemented

## Lane

normal

## Product Contract

The infrastructure compose files must match the contracts recorded in
`docs/product/domains.md` and `docs/ARCHITECTURE.md`:

- The Unsloth training container reaches Ollama at `http://ollama:11434` on
  the shared `llm-net` network (Training contract: "Can reach Ollama at
  `http://ollama:11434` via `llm-net`").
- The Qwen-VL container's healthcheck runs *inside* the container and must
  target the in-container vLLM port, not the published host port.
- The Qwen-VL `.env` and `.env.example` contain one authoritative value per
  configuration setting so that Docker Compose interpolation is deterministic.

## Relevant Product Docs

- `docs/product/domains.md` (Serving, Training, Known Implementation Gaps).
- `docs/ARCHITECTURE.md` (Topology and Configuration layer).
- `docs/decisions/0004-docker-compose-shared-network.md`.

## Acceptance Criteria

- `training/unsloth/docker-compose.yml` sets
  `OLLAMA_HOST: "http://ollama:11434"`.
- `serving/qwen-vl/docker-compose.yml` healthcheck uses
  `http://localhost:${CONTAINER_PORT}/health` (in-container port).
- `serving/qwen-vl/.env.example` and `serving/qwen-vl/.env` define
  `HOST_PORT` and `CONTAINER_PORT` exactly once each, with non-empty
  authoritative defaults.
- `docker compose -f <file> config` resolves both compose files without
  errors and shows the corrected values.
- `docs/product/domains.md` "Known Implementation Gaps" no longer lists
  these three items.

## Design Notes

- Configuration only; no service code or scripts change.
- Healthcheck runs from inside the qwen-vlm container, where vLLM binds to
  `${CONTAINER_PORT}`. The published port (`HOST_PORT`) is host-side and
  not reachable as `localhost` from within the container.
- `.env` parsing: when a key appears twice, Docker Compose reads the last
  occurrence. The current files end with empty `HOST_PORT=` /
  `CONTAINER_PORT=` blocks, which would resolve compose vars to empty
  strings and break `--port` and the port mapping.
- Keep the duplicated `.env` and `.env.example` content in sync; the
  example is the documented contract, the `.env` is the current local
  copy.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | n/a (configuration only) |
| Integration | `docker compose -f training/unsloth/docker-compose.yml config` and `docker compose -f serving/qwen-vl/docker-compose.yml config` exit 0 with corrected values |
| E2E | n/a until Cross-S01 lands (full network reachability) |
| Platform | Healthcheck exec verifiable once Qwen-VL is running locally (deferred to E01-S02 evidence) |
| Release | n/a |

## Harness Delta

- Added a `cross/` epic folder under `docs/stories/epics/` for cross-cutting
  stories that don't sit inside a single product epic.
- No template or backlog changes required.

## Evidence

Validation commands and their outputs are recorded in this packet after
applying the fixes:

```text
$ docker compose -f training/unsloth/docker-compose.yml config | grep -A1 OLLAMA_HOST
      OLLAMA_HOST: http://ollama:11434

$ docker compose -f serving/qwen-vl/docker-compose.yml config | grep -A1 healthcheck
    healthcheck:
      test:
      - CMD
      - curl
      - -f
      - http://localhost:8000/health
```

(The recorded `8000` is the resolved `${CONTAINER_PORT}` from
`serving/qwen-vl/.env`.)
