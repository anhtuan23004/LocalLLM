# E07-S01 Minimal LiteLLM Gateway

## Status

implemented

## Lane

normal

## Product Contract

LiteLLM runs as a Docker Compose service on `llm-net` and exposes a local
OpenAI-compatible gateway. The first gateway route is `local-ollama`, which
forwards requests to Ollama at `http://ollama:11434`.

Direct runtime access to Ollama remains available.

## Relevant Product Docs

- `docs/product/domains.md` (Serving).
- `docs/ARCHITECTURE.md` (Topology).
- `docs/stories/initiatives/litellm-gateway.md`.

## Acceptance Criteria

- `serving/litellm/docker-compose.yml` starts a LiteLLM proxy on `llm-net`.
- LiteLLM exposes host port `18040` by default and container port `4000`.
- `serving/litellm/config.yaml` defines the `local-ollama` route.
- `serving/litellm/.env.example` documents the local environment contract.
- `./llm-local serve litellm up` and `./llm-local serve litellm down` manage
  the gateway.
- Makefile targets exist for `litellm-up` and `litellm-down`.
- Static validation includes the LiteLLM compose file.

## Design Notes

- LiteLLM image: `docker.litellm.ai/berriai/litellm:v1.72.6-stable` by
  default.
- Gateway host port: `18040`.
- Gateway model alias: `local-ollama`.
- Upstream model env var: `OLLAMA_LITELLM_MODEL`, default
  `ollama_chat/llama3`.
- Upstream base URL env var: `OLLAMA_API_BASE`, default
  `http://ollama:11434`.
- Proxy auth env var: `LITELLM_MASTER_KEY`, default `sk-local-litellm`.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `bash -n llm-local` passes |
| Integration | `docker compose -f serving/litellm/docker-compose.yml config`; `make validate-compose`; `./llm-local smoke`; `/v1/chat/completions` through `local-ollama` on VPS |
| E2E | `/v1/models` gateway smoke passes |
| Platform | n/a |
| Release | n/a |

## Harness Delta

- Added this story packet.
- Added `E07-S01` to `docs/TEST_MATRIX.md`.
- Updated the LiteLLM initiative and story backlog links.

## Evidence

```bash
$ docker compose -f serving/litellm/docker-compose.yml config
# exits 0 and resolves the LiteLLM service, config mount, host port 18040,
# env-backed Ollama route settings, and external llm-net network.

$ make validate-compose
# exits 0 and includes serving/litellm/docker-compose.yml.

$ bash -n llm-local
# exits 0.

$ ./llm-local smoke
# exits 0 and includes serving/litellm compose validation.

$ ./llm-local serve litellm up
# pulls/starts docker.litellm.ai/berriai/litellm:v1.72.6-stable on first run

$ curl -fsS -H "Authorization: Bearer sk-local-litellm" http://localhost:18040/v1/models
{"data":[{"id":"local-ollama","object":"model","created":1677610602,"owned_by":"openai"}],"object":"list"}

$ curl -fsS -X POST http://localhost:18040/v1/chat/completions \
    -H "Authorization: Bearer sk-local-litellm" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "local-ollama",
      "messages": [{"role": "user", "content": "Xin chao, tra loi ngan gon."}]
    }'
{"id":"chatcmpl-ce3053b5-71a6-4550-9a99-1d20670694ed","created":1779444613,"model":"local-ollama","object":"chat.completion","choices":[{"finish_reason":"stop","index":0,"message":{"content":"Xin chào! Tôi có thể giúp gì cho bạn hôm nay?","role":"assistant"}}],"usage":{"completion_tokens":16,"prompt_tokens":40,"total_tokens":56}}

$ ./llm-local serve litellm down
# stops and removes the litellm container
```

Chat completion proof was provided from the user's VPS with Ollama running and
the configured `local-ollama` model available.

After E07-S02, `/v1/models` also returns `local-vllm`, `local-sglang`,
`local-llama-cpp`, and `local-mlx`.
