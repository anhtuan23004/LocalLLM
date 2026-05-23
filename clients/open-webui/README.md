# Open WebUI Client

Open WebUI is the browser UI for LLM-Local. In this repo it is a client of
LiteLLM, not a source of runtime configuration.

## Configure

```bash
cp clients/open-webui/.env.example clients/open-webui/.env
```

Defaults:

```dotenv
HOST_PORT=18088
OPENAI_API_BASE_URL=http://litellm:4000/v1
OPENAI_API_KEY=sk-local-litellm
ENABLE_OLLAMA_API=false
ENABLE_OPENAI_API=true
```

Keep `OPENAI_API_KEY` aligned with `serving/litellm/.env`
`LITELLM_MASTER_KEY`.

## Run

Start at least one backend model, then LiteLLM, then Open WebUI:

```bash
./llm-local serve ollama up
./llm-local serve litellm up
./llm-local webui up
```

Open:

```text
http://localhost:18088
```

On first launch with `WEBUI_AUTH=true`, create the first local admin account in
the browser. The first account owns the local Open WebUI instance.

## Smoke

Check Open WebUI is reachable:

```bash
curl -fsS http://localhost:${HOST_PORT:-18088}/health
```

Check LiteLLM model list directly:

```bash
curl -fsS -H "Authorization: Bearer ${OPENAI_API_KEY:-sk-local-litellm}" \
  http://localhost:18040/v1/models
```

In the UI:

1. Sign in or create the first local admin account.
2. Open the model selector.
3. Confirm LiteLLM aliases such as `local-ollama` appear.
4. Send a short prompt through `local-ollama`.

## Stop

```bash
./llm-local webui down
```

Open WebUI state is persisted in the Docker volume
`open-webui_open_webui_data`.
