# E07-S02 LiteLLM Multi-Runtime Routing

## Status

implemented

## Lane

normal

## Product Contract

LiteLLM exposes stable local aliases for the repo's serving runtimes:
`local-ollama`, `local-vllm`, `local-sglang`, `local-llama-cpp`, and
`local-mlx`. Each alias keeps direct runtime access available and routes through
environment-specific upstream URLs and model strings.

## Relevant Product Docs

- `docs/product/domains.md` (Serving).
- `docs/ARCHITECTURE.md` (Topology).
- `docs/stories/initiatives/litellm-gateway.md`.
- `serving/litellm/README.md`.

## Acceptance Criteria

- `serving/litellm/config.yaml` defines all five `local-*` aliases.
- `serving/litellm/.env.example` documents API bases, model strings, and local
  upstream API keys.
- `serving/litellm/docker-compose.yml` passes the alias env values into the
  LiteLLM container.
- Alias preconditions are documented for each runtime.
- Direct runtime endpoints remain unchanged.

## Design Notes

- OpenAI-compatible backends use LiteLLM `openai/<served-model>` provider
  strings and upstream `/v1` base URLs.
- `local-mlx` targets `host.docker.internal:18081` because MLX-LM is a host
  process, not a Docker service on `llm-net`.
- Non-Ollama runtime request proof is deferred until those backend services are
  running with model names matching the LiteLLM env values.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | YAML parse for `serving/litellm/config.yaml` passes |
| Integration | `docker compose -f serving/litellm/docker-compose.yml config` resolves all alias env values |
| E2E | `/v1/models` returns all aliases from the running gateway |
| Platform | Runtime request proof deferred to prepared backend containers |
| Release | `./llm-local smoke` includes LiteLLM compose validation |

## Harness Delta

- Added this story packet.
- Added `E07-S02` to `docs/TEST_MATRIX.md`.
- Updated the LiteLLM initiative and story backlog link.

## Evidence

```bash
$ python3 - <<'PY'
import pathlib
import yaml
path = pathlib.Path('serving/litellm/config.yaml')
with path.open() as f:
    yaml.safe_load(f)
print(f'{path}: ok')
PY
# exits 0

$ docker compose -f serving/litellm/docker-compose.yml config
# exits 0 and resolves local-ollama, local-vllm, local-sglang,
# local-llama-cpp, and local-mlx environment values.

$ ./llm-local serve litellm up
# starts the LiteLLM gateway

$ curl -fsS -H "Authorization: Bearer sk-local-litellm" http://localhost:18040/v1/models
{"data":[{"id":"local-ollama","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-vllm","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-sglang","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-llama-cpp","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-mlx","object":"model","created":1677610602,"owned_by":"openai"}],"object":"list"}

$ ./llm-local serve litellm down
# stops and removes the litellm container
```

Runtime request proof through `local-vllm`, `local-sglang`,
`local-llama-cpp`, and `local-mlx` remains deferred until those runtimes are
running with matching served model names.
