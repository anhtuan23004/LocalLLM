# E01-S01 Ollama serves chat completions

## Status

implemented

## Lane

normal

## Product Contract

Ollama serves chat completions on llm-net.

## Relevant Product Docs

- `docs/product/overview.md`

## Acceptance Criteria

- Ollama container starts correctly and exposes port 11434.
- Ollama endpoint responds to `/api/generate` properly on llm-net.

## Design Notes

- Commands: `ollama pull <model>`, `docker compose up -d`
- Queries: curl `http://localhost:11434/api/generate`

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | |
| Integration | curl to `/api/generate` returns 200 |
| E2E | |
| Platform | |
| Release | |

## Harness Delta

N/A

## Evidence

Ran:
```
cd serving/ollama
docker compose up -d
docker exec ollama ollama pull qwen2.5:0.5b
curl -X POST http://localhost:11434/api/generate -d '{"model": "qwen2.5:0.5b", "prompt": "Why is the sky blue?", "stream": false}'
```
Received JSON string indicating `done: true` and a valid generated response.
