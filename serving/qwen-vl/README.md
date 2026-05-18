# Qwen3-4B-VL OCR Deployment

This project provides a Dockerized setup to run **Qwen3-4B-VL** with **vLLM**

---

## Requirements

* Docker & Docker Compose installed
* GPU with CUDA support
* vLLM API running (inside Docker)

---

## Project Structure

```
vllmocrexp/
├── docker-compose.yml
├── models/          # optional, local model storage
```

---

## Configuration

Create a `.env` file in the `QwenVL` directory to configure your environment. You can copy the example below:

```bash
# Local path to the models directory
MODEL_LOCAL_PATH=path/to/models

# Hugging Face Token (optional)
# HF_TOKEN=your_token_here

# GPU Device IDs to use
CUDA_VISIBLE_DEVICES=0
```

---

## Setup & Deployment

1.  **Pull the Docker image**

```bash
docker pull vllm/vllm-openai:v0.11.0
```

2.  **Build and start the containers**

```bash
cd QwenVL
# Ensure your .env file is configured
docker compose up
# OR run in detached mode
docker compose up -d
```

* `qwen-vlm` container runs the Qwen3-4B-VL model with vLLM

3.  **Clean-up**

To remove temporary files, Docker volumes, and images:

```bash
docker compose down -v
rm -rf tmp/
```
