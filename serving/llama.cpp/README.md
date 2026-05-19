# llama.cpp Serving

llama.cpp serves GGUF models through `llama-server`.

```bash
cp serving/llama.cpp/.env.example serving/llama.cpp/.env
# Edit LLAMA_CPP_MODEL_PATH to point at a real .gguf file under /models.
cd serving/llama.cpp && docker compose up -d
curl http://localhost:8080/v1/models
```

Use `LLAMA_CPP_IMAGE_TAG=server` for CPU-only runs or `server-cuda` for NVIDIA
GPU offload.

