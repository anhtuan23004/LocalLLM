# E01-S02 vLLM OpenAI-compatible serving validation

## Status

planned

## Lane

normal

## Product Contract

vLLM starts with repository `.env` configuration, serves the configured model,
passes its healthcheck, and responds through its OpenAI-compatible API.

## Relevant Product Docs

- `docs/product/domains.md` (Serving).
- `serving/vllm/README.md`.
- `docs/TEST_MATRIX.md` (E01-S02 proof row).

## Acceptance Criteria

- `serving/vllm/.env.example` documents the minimum runtime configuration for a
  prepared GPU host.
- `docker compose -f serving/vllm/docker-compose.yml config` resolves the vLLM
  service with model, served-model name, port, GPU, and healthcheck settings.
- `./llm-local serve vllm up` starts vLLM on a prepared CUDA host.
- vLLM healthcheck reaches `http://localhost:8000/health` inside the container.
- Host endpoint `http://localhost:18000/v1/chat/completions` returns a valid
  OpenAI-compatible chat completion for the configured served model.

## Design Notes

- This is the next prioritized story because vLLM is a core serving runtime and
  later evaluation, observability, and LiteLLM workflows depend on a validated
  OpenAI-compatible backend.
- Full runtime proof requires a prepared CUDA host with compatible NVIDIA
  driver, model files, and enough VRAM for the selected model.
- Static compose proof can run anywhere Docker Compose is available, but it is
  not enough to mark the story implemented.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | n/a |
| Integration | `docker compose -f serving/vllm/docker-compose.yml config`; `curl` to `/v1/chat/completions` succeeds against running vLLM |
| E2E | n/a |
| Platform | Container healthcheck reports healthy on prepared CUDA host |
| Release | n/a |

## Harness Delta

- Marked E01-S02 as the next prioritized story in the backlog.
- Clarified that the planned matrix row requires integration and platform
  proof before implementation.

## Evidence

Pending. Do not mark implemented until the runtime command output is recorded.
