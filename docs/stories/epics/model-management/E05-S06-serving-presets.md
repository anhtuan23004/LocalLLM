# E05-S06 Serving Presets

## Status

implemented

## Lane

normal

## Product Contract

Serving presets provide workflow-level model switching while preserving
runtime-level model control. A preset binds a model, serving runtime, and LiteLLM
gateway alias so user-facing clients can keep stable `local-*` model names.

## Relevant Product Docs

- `CONTEXT.md`
- `docs/product/domains.md`
- `docs/decisions/0006-serving-presets.md`

## Acceptance Criteria

- `models/presets.yaml` defines serving presets as data, not hard-coded CLI
  branches.
- `./llm-local preset list` lists configured presets.
- `./llm-local preset show <id>` prints one preset.
- `./llm-local preset apply <id>` writes generated local active state to
  `config/active/serving.yaml`.
- `./llm-local preset apply <id> --dry-run` reports planned changes without
  writing active state or runtime `.env` files.
- `./llm-local config render` renders the active preset into runtime `.env`
  model values.
- Presets targeting vLLM, SGLang, llama.cpp, or MLX reuse runtime-level model
  selection instead of duplicating runtime `.env` logic.
- Existing `./llm-local model select <id> --runtime <runtime>` remains available
  for power users.
- Documentation uses **Serving Preset** for model workflow switching and avoids
  overloading Docker Compose **profile** terminology.

## Design Notes

- `models/presets.py` is intentionally data-driven. Adding a new workflow should
  normally mean editing `models/presets.yaml`.
- `config/active/serving.yaml` is generated local state and is not tracked.
- Ollama presets can provide a `setup_hint` because Ollama model storage is
  separate from the repo's bind-mounted `models/` directory.
- `--render` renders the active state into runtime `.env` files immediately.
- `--restart` renders, then restarts the affected runtime and LiteLLM.
- `--pull` is explicit for Ollama so applying a preset does not unexpectedly
  download model weights.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `uv run python -m py_compile models/presets.py` |
| Integration | `./llm-local preset list`; `./llm-local preset show chat-small`; `./llm-local preset apply chat-small --dry-run --render`; `./llm-local smoke` |
| E2E | Not required; browser clients consume LiteLLM aliases |
| Platform | Runtime restart/pull behavior deferred to prepared host |
| Release | `make validate`; `./llm-local smoke` |

## Harness Delta

The domain glossary now defines **Serving Preset**, **Gateway Alias**, and the
distinction from Docker Compose **Compose Profile**.

## Evidence

Validation after implementation:

```bash
bash -n llm-local
uv run python -m py_compile models/presets.py models/manage.py models/validate_registry.py scripts/preflight.py
./llm-local preset list
./llm-local preset show chat-small
./llm-local preset apply chat-small --dry-run --render
./llm-local preset apply glm-ocr-vllm --dry-run
./llm-local preset apply glm-ocr-sglang --dry-run
./llm-local smoke
make validate
```
