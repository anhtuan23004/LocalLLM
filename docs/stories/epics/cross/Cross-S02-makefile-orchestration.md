# Cross-S02 Top-Level Makefile Orchestration

## Status

implemented

## Lane

tiny

## Product Contract

A top-level `Makefile` provides shortcut targets for the core loop and all
service lifecycle operations without introducing a monolithic compose file.

## Relevant Product Docs

- `docs/ARCHITECTURE.md` (Topology, Dependency Rule)

## Acceptance Criteria

- `make help` lists all targets with descriptions.
- Core loop targets: `network`, `ollama-up`, `benchmark-ollama`, `observe-batch`, `validate-compose`.
- `PROMPT` variable is shell-safe (quoted in commands).
- `validate-compose` checks all compose configs parse without error.
- `validate-health` checks running container healthchecks.
- No "start everything" as default goal — `help` is default.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `make help` exits 0 and lists targets |
| Integration | `make validate-compose` passes when compose files are valid |

## Evidence

```bash
$ make help
  network              Create llm-net Docker network
  ollama-up            Start Ollama
  benchmark-ollama     Benchmark Ollama (MODEL=x N=x)
  ...

$ make validate-compose
docker compose -f serving/ollama/docker-compose.yml config >/dev/null
docker compose -f serving/vllm/docker-compose.yml config >/dev/null
...
All compose configs valid.
```
