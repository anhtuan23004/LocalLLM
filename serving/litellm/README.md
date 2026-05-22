# LiteLLM Gateway

LiteLLM runs as the local OpenAI-compatible gateway for LLM-Local. It exposes
stable client-facing aliases while forwarding requests to the selected local
runtime.

## Configure

```bash
cp serving/litellm/.env.example serving/litellm/.env
```

Edit `serving/litellm/.env` for your local model and key:

```dotenv
LITELLM_MASTER_KEY=sk-local-litellm
OLLAMA_API_BASE=http://ollama:11434
OLLAMA_LITELLM_MODEL=ollama_chat/llama3
VLLM_API_BASE=http://vllm:8000/v1
VLLM_LITELLM_MODEL=openai/Qwen/Qwen3-VL-4B-Instruct
```

`config.yaml` stores the public route shape and reads sensitive or
environment-specific values from environment variables.

Configured aliases:

| Alias | Upstream | Preconditions |
| --- | --- | --- |
| `local-ollama` | `http://ollama:11434` | Ollama is running and has the configured model pulled. |
| `local-vllm` | `http://vllm:8000/v1` | vLLM is running with `VLLM_LITELLM_MODEL` matching the served model name. |
| `local-sglang` | `http://sglang:30000/v1` | SGLang is running with `SGLANG_LITELLM_MODEL` matching the served model name. |
| `local-llama-cpp` | `http://llama-cpp:8080/v1` | llama.cpp is running with alias `local-gguf` or matching `LLAMA_CPP_LITELLM_MODEL`. |
| `local-mlx` | `http://host.docker.internal:18081/v1` | MLX-LM is running on the host through `serving/mlx/serve.sh`. |

## Run

```bash
./llm-local serve ollama up
./llm-local serve litellm up
```

List configured LiteLLM models:

```bash
curl -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-local-litellm}" \
  http://localhost:${HOST_PORT:-18040}/v1/models
```

Send a chat completion through the gateway:

```bash
curl -X POST "http://localhost:${HOST_PORT:-18040}/v1/chat/completions" \
  -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-local-litellm}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-ollama",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}]
  }'
```

Direct runtime access remains available through the Ollama service.

LiteLLM Prometheus metrics are enabled through the `prometheus` callback and
are exposed at:

```bash
curl http://localhost:${HOST_PORT:-18040}/metrics/
```
