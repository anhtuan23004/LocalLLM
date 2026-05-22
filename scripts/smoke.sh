#!/usr/bin/env bash
# scripts/smoke.sh — Regression guard for LLM-Local infrastructure.
# Default mode checks static configuration and local scripts only.
# Use --runtime to additionally check running service health/endpoints.
# Exit 0 = all pass, exit 1 = failures found.

set -uo pipefail

PASS=0
FAIL=0
RUNTIME=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/smoke.sh [--runtime]

Default checks:
  - Docker Compose config resolution
  - model registry and conversion script presence
  - shell syntax for repo scripts
  - Grafana dashboard JSON validity
  - Makefile help target

Runtime checks with --runtime:
  - llm-net exists
  - running Ollama/vLLM health
  - local inference and observability endpoints
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --runtime) RUNTIME=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

if [ -f observation/.env ]; then
  while IFS='=' read -r key value; do
    case "$key" in
      ""|\#*) continue ;;
    esac
    if [ -z "${!key+x}" ]; then
      export "$key=$value"
    fi
  done < observation/.env
fi

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf "  ✓ %s\n" "$label"
    PASS=$((PASS + 1))
  else
    printf "  ✗ %s\n" "$label"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Compose Configs ==="
check "serving/ollama" docker compose -f serving/ollama/docker-compose.yml config
check "serving/vllm" docker compose -f serving/vllm/docker-compose.yml config
check "serving/sglang" docker compose -f serving/sglang/docker-compose.yml config
check "serving/llama.cpp" docker compose -f serving/llama.cpp/docker-compose.yml config
check "training/unsloth" docker compose -f training/unsloth/docker-compose.yml config
check "evaluation" docker compose -f evaluation/docker-compose.yml config
check "observation" docker compose -f observation/docker-compose.yml config

echo "=== Model Registry ==="
check "registry.yaml exists" test -f models/registry.yaml
check "convert.sh executable" test -x models/convert.sh
check "validate_registry.py exists" test -f models/validate_registry.py
check "registry validates" ./llm-local model validate

echo "=== Scripts ==="
check "convert.sh syntax" bash -n models/convert.sh
check "validate_registry.py syntax" uv run python -m py_compile models/validate_registry.py
check "ollama_exporter.py syntax" uv run python -m py_compile observation/scripts/ollama_exporter.py
check "run_lm_eval.sh syntax" sh -n evaluation/scripts/run_lm_eval.sh
check "mlx serve.sh syntax" bash -n serving/mlx/serve.sh
check "smoke.sh syntax" bash -n scripts/smoke.sh

echo "=== Dashboards ==="
check "Grafana dashboard JSON" python3 -m json.tool observation/grafana/dashboards/llm-local-overview.json

echo "=== Makefile ==="
check "make help" make help

if [ "$RUNTIME" -eq 1 ]; then
  echo "=== Runtime Network ==="
  check "llm-net exists" docker network inspect llm-net

  echo "=== Serving Health ==="
  check "Ollama healthy" sh -c 'docker inspect --format="{{.State.Health.Status}}" ollama 2>/dev/null | grep -q healthy'
  check "vLLM healthy" sh -c 'docker inspect --format="{{.State.Health.Status}}" vllm 2>/dev/null | grep -q healthy'

  echo "=== Inference ==="
  check "Ollama responds" curl -sf "http://localhost:${OLLAMA_HOST_PORT:-18134}/api/tags"
  check "vLLM responds" curl -sf "http://localhost:${VLLM_HOST_PORT:-18000}/health"

  echo "=== Observability ==="
  check "Prometheus up" curl -sf "http://localhost:${PROMETHEUS_HOST_PORT:-9090}/-/healthy"
  check "Grafana up" curl -sf "http://localhost:${GRAFANA_HOST_PORT:-3000}/api/health"
else
  echo "=== Runtime Checks ==="
  echo "  skipped (run ./scripts/smoke.sh --runtime to check live services)"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
