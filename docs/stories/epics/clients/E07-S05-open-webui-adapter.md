# E07-S05 Open WebUI Adapter

## Status

implemented

## Lane

normal

## Product Contract

Open WebUI runs as a Docker Compose service on `llm-net` and provides the local
browser UI for interactive model use. It connects to LiteLLM at
`http://litellm:4000/v1` as an OpenAI-compatible provider.

Open WebUI is a client of the LiteLLM gateway. It is not the source of runtime
configuration truth for Ollama, vLLM, SGLang, llama.cpp, or MLX-LM.

## Relevant Product Docs

- `docs/product/domains.md` (Serving and interactive client contract).
- `docs/ARCHITECTURE.md` (Topology).
- `docs/stories/initiatives/litellm-gateway.md`.
- `clients/open-webui/README.md`.

## Acceptance Criteria

- `clients/open-webui/docker-compose.yml` defines an Open WebUI service on
  `llm-net`.
- The service exposes host port `18088` by default and container port `8080`.
- Open WebUI points to LiteLLM through
  `OPENAI_API_BASE_URL=http://litellm:4000/v1`.
- Open WebUI sends `OPENAI_API_KEY` matching the local LiteLLM master key.
- Direct Ollama integration is disabled by default so model access flows through
  LiteLLM.
- `./llm-local webui up` and `./llm-local webui down` manage the client.
- Makefile targets exist for `open-webui-up` and `open-webui-down`.
- Static validation includes the Open WebUI compose file.

## Design Notes

- Open WebUI image: `ghcr.io/open-webui/open-webui:main` by default.
- Gateway URL: `http://litellm:4000/v1`.
- Gateway API key: `sk-local-litellm` by default.
- Browser URL: `http://localhost:18088`.
- State persists in Docker volume `open-webui_open_webui_data`.
- `WEBUI_AUTH` defaults to `true`; the first browser user becomes the local
  admin account.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `bash -n llm-local`; `bash -n scripts/smoke.sh` |
| Integration | `docker compose -f clients/open-webui/docker-compose.yml config`; `make validate-compose`; `./llm-local smoke` |
| E2E | Browser page serves locally; first-account login and chat prompt remain manual |
| Platform | Host port conflicts checked through Docker published ports at runtime |
| Release | n/a |

## Harness Delta

- Added this story packet.
- Added `E07-S05` to `docs/TEST_MATRIX.md`.
- Updated the LiteLLM initiative and story backlog link.

## Evidence

```bash
$ docker compose -f clients/open-webui/docker-compose.yml config
# exits 0 and resolves Open WebUI, host port 18088, llm-net, and LiteLLM
# OpenAI-compatible provider env values.

$ bash -n llm-local
# exits 0.

$ bash -n scripts/smoke.sh
# exits 0.

$ make validate-compose
# exits 0 and includes clients/open-webui/docker-compose.yml.

$ ./llm-local smoke
# exits 0 with Results: 21 passed, 0 failed.

$ ./llm-local webui up
# pulls ghcr.io/open-webui/open-webui:main on first run and starts open-webui.

$ curl -fsS http://localhost:18088/health
{"status":true}

$ curl -fsS http://localhost:18088/ | head -n 5
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8" />
		<link rel="icon" type="image/png" href="/static/favicon.png" crossorigin="use-credentials" />

$ ./llm-local serve litellm up
# starts LiteLLM on llm-net.

$ docker exec open-webui python -c 'import urllib.request; req=urllib.request.Request("http://litellm:4000/v1/models", headers={"Authorization":"Bearer sk-local-litellm"}); print(urllib.request.urlopen(req, timeout=10).read().decode())'
{"data":[{"id":"local-ollama","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-vllm","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-sglang","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-llama-cpp","object":"model","created":1677610602,"owned_by":"openai"},{"id":"local-mlx","object":"model","created":1677610602,"owned_by":"openai"}],"object":"list"}
```

Open WebUI is serving the browser UI and can reach LiteLLM's model list from
inside the client container. The remaining manual browser smoke is:

```text
1. Open http://localhost:18088.
2. Create or sign in to the first local admin account.
3. Confirm the model selector lists LiteLLM aliases such as local-ollama.
4. Send a short chat prompt through local-ollama.
```
