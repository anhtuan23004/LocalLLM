# LLM-Local

Local LLM infrastructure for serving, training, evaluation, and observation.

## Directory Structure

```
├── models/              Shared model weights + download script
├── datasets/            Shared training datasets
├── serving/             Model serving services
│   ├── ollama/          Ollama (general LLM serving)
│   └── vllm/            vLLM OpenAI-compatible serving
├── training/            Model training/fine-tuning
│   └── unsloth/         Unsloth fine-tuning environment
├── evaluation/          Benchmark and evaluation tools
└── observation/         Metrics collection and visualization
```

## Prerequisites

Create the shared Docker network:

```bash
docker network create llm-net
```

## Usage

### Download Models

```bash
python models/download_model.py <model_id> --dir models
# Example: python models/download_model.py Qwen/Qwen3-VL-4B-Instruct --dir models
```

### Start Services

```bash
# Ollama
cd serving/ollama && docker compose up -d

# vLLM (configure .env first)
cd serving/vllm && docker compose up -d

# Unsloth training
cd training/unsloth && docker compose up -d
```

### Run Evaluation

```bash
cd evaluation && docker compose run --rm evaluation \
  --endpoint http://ollama:11434 \
  --model-name llama3 \
  --num-requests 20
```

### View Observation

```bash
cd observation && docker compose run --rm observation
```

Results are saved to `evaluation/results/` and visualizations to `observation/dashboards/`.
