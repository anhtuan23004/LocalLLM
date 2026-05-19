.PHONY: network ollama-up ollama-down vllm-up vllm-down \
       sglang-up sglang-down llama-cpp-up llama-cpp-down mlx-up \
       train-up train-down \
       observe-up observe-down observe-batch \
       benchmark-ollama benchmark-vllm eval-quality \
       validate validate-compose validate-health validate-registry \
       smoke down help

MODEL ?= llama3
N ?= 10
PROMPT ?= "Explain briefly what a neural network is."

# --- Serving ---

network: ## Create llm-net Docker network
	docker network create llm-net 2>/dev/null || true

ollama-up: ## Start Ollama
	./llm-local serve ollama up

ollama-down:
	./llm-local serve ollama down

vllm-up: ## Start vLLM
	./llm-local serve vllm up

vllm-down:
	./llm-local serve vllm down

sglang-up: ## Start SGLang
	./llm-local serve sglang up

sglang-down:
	./llm-local serve sglang down

llama-cpp-up: ## Start llama.cpp server
	./llm-local serve llama.cpp up

llama-cpp-down:
	./llm-local serve llama.cpp down

mlx-up: ## Start MLX-LM server on host
	./llm-local serve mlx up

# --- Training ---

train-up: ## Start Unsloth training environment
	./llm-local train up

train-down:
	./llm-local train down

# --- Observation ---

observe-up: ## Start real-time monitoring (Prometheus + Grafana)
	./llm-local observe up

observe-down:
	./llm-local observe down

observe-batch: ## Generate batch report from benchmark results
	./llm-local observe batch

# --- Evaluation ---

benchmark-ollama: ## Benchmark Ollama (MODEL=x N=x)
	./llm-local eval run --target ollama --model $(MODEL) --num-requests $(N) --prompt "$(PROMPT)"

benchmark-vllm: ## Benchmark vLLM (MODEL=x N=x)
	./llm-local eval run --target vllm --model $(MODEL) --num-requests $(N) --prompt "$(PROMPT)"

eval-quality: ## Run lm-eval quality benchmark against vLLM
	./llm-local eval quality

# --- Validation ---

validate-compose: ## Verify all docker-compose configs are valid
	docker compose -f serving/ollama/docker-compose.yml config >/dev/null
	docker compose -f serving/vllm/docker-compose.yml config >/dev/null
	docker compose -f serving/sglang/docker-compose.yml config >/dev/null
	docker compose -f serving/llama.cpp/docker-compose.yml config >/dev/null
	docker compose -f training/unsloth/docker-compose.yml config >/dev/null
	docker compose -f evaluation/docker-compose.yml config >/dev/null
	docker compose -f observation/docker-compose.yml config >/dev/null
	@echo "All compose configs valid."

validate-health: ## Check running container healthchecks
	@echo "Checking Ollama..." && docker inspect --format='{{.State.Health.Status}}' ollama 2>/dev/null || echo "not running"
	@echo "Checking vLLM..." && docker inspect --format='{{.State.Health.Status}}' vllm 2>/dev/null || echo "not running"

validate-registry: ## Check model registry paths
	./llm-local model validate

validate: validate-compose validate-registry ## Run all validations

smoke: ## Run lightweight regression smoke test
	./llm-local smoke

# --- Lifecycle ---

down: ## Stop all services
	-./llm-local serve ollama down
	-./llm-local serve vllm down
	-./llm-local serve sglang down
	-./llm-local serve llama.cpp down
	-./llm-local train down
	-./llm-local observe down

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
