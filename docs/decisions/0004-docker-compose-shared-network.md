# 0004 Docker Compose with Shared External Network

Date: 2026-05-18

## Status

Accepted

## Context

LLM-Local needs multiple services (serving, training, evaluation, observation)
to communicate. Each service has its own lifecycle — you may want Ollama running
permanently but only spin up evaluation on demand.

A single monolithic docker-compose.yml would force all services to start/stop
together and complicate GPU allocation. Separate compose files per domain give
independent lifecycle control but need a connectivity mechanism.

## Decision

Use independent Docker Compose stacks per domain, all joining a shared external
network named `llm-net`.

The network is created once manually:

```bash
docker network create llm-net
```

Each compose file declares:

```yaml
networks:
  llm-net:
    external: true
```

Services reference each other by container name (e.g., `http://ollama:11434`).

## Alternatives Considered

1. Single docker-compose.yml with profiles. Rejected because GPU allocation
   differs per service and independent lifecycle is more practical for
   development.
2. Docker Compose `depends_on` across files. Not supported natively; would
   require wrapper scripts.
3. Host networking. Rejected because port conflicts are likely and container
   name resolution is lost.

## Consequences

Positive:

- Each domain starts/stops independently.
- GPU resources allocated per-service without conflict.
- Services discover each other by container name.
- Easy to add new services — just join `llm-net`.
- No orchestration tool required beyond Docker Compose.

Tradeoffs:

- Manual `docker network create llm-net` prerequisite (one-time).
- No built-in dependency ordering across stacks.
- Health of upstream services must be checked by consumers, not guaranteed by compose.

## Follow-Up

- Consider a top-level orchestration compose or Makefile for common workflows.
- Add a pre-check script that ensures `llm-net` exists before starting services.
