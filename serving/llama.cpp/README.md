# llama.cpp Serving

llama.cpp serves GGUF models through `llama-server`.

```bash
cp serving/llama.cpp/.env.example serving/llama.cpp/.env
# Edit LLAMA_CPP_MODEL_PATH to point at a real .gguf file under /models.
# For vision models, also set LLAMA_CPP_MMPROJ_PATH to the matching mmproj GGUF.
cd serving/llama.cpp && docker compose up -d
curl http://localhost:18080/v1/models
```

Use `LLAMA_CPP_IMAGE_TAG=server` for CPU-only runs or `server-cuda` for NVIDIA
GPU offload.

## Model Types

Text-only GGUF models need only `LLAMA_CPP_MODEL_PATH`:

```env
LLAMA_CPP_MODEL_PATH=/models/<model-dir>/<model>.gguf
LLAMA_CPP_MMPROJ_PATH=
```

Vision models require both the base GGUF and a matching multimodal projector:

```env
LLAMA_CPP_MODEL_PATH=/models/<model-dir>/gguf/Qwen3-VL-2B-Instruct-Vietnamese.Q4_K_M.gguf
LLAMA_CPP_MMPROJ_PATH=/models/<model-dir>/gguf/Qwen3-VL-2B-Instruct-Vietnamese.mmproj.gguf
```

Ollama packages this detail internally, and vLLM/SGLang use Hugging Face model
config directly. The explicit `mmproj` path is specific to llama.cpp vision
GGUF serving.

## Example: Qwen3-VL Vietnamese GGUF

Download the GGUF files:

```bash
export HF_TOKEN=...
huggingface-cli download \
  minhduc168/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit-Vietnamese \
  --include "gguf/*" \
  --local-dir models/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit-Vietnamese
```

Configure `serving/llama.cpp/.env`:

```env
MODEL_LOCAL_PATH=../../models
HOST_PORT=18080
CONTAINER_PORT=8080
LLAMA_CPP_IMAGE_TAG=server-cuda
LLAMA_CPP_MODEL_PATH=/models/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit-Vietnamese/gguf/Qwen3-VL-2B-Instruct-Vietnamese.Q4_K_M.gguf
LLAMA_CPP_MMPROJ_PATH=/models/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit-Vietnamese/gguf/Qwen3-VL-2B-Instruct-Vietnamese.mmproj.gguf
LLAMA_CPP_CTX_SIZE=4096
LLAMA_CPP_N_PARALLEL=1
LLAMA_CPP_N_GPU_LAYERS=99
```

Start and test:

```bash
./llm-local serve llama.cpp up
curl http://localhost:18080/v1/models
```

For image requests, include the llama.cpp multimodal marker `<__media__>` in
the text part:

```bash
IMG_B64="$(base64 -i ./test.png | tr -d '\n')"

curl http://localhost:18080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"local-gguf\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": [
        {\"type\":\"text\",\"text\":\"<__media__> Extract invoice_number and total_amount. Return only JSON.\"},
        {\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,$IMG_B64\"}}
      ]
    }],
    \"max_tokens\": 512
  }"
```
