# 0006 — Serving Presets for Workflow-Level Model Switching

## Status

accepted

## Context

LLM-Local has two model selection needs. Power users need runtime-level control
through commands such as `model select --runtime vllm`, while regular users need
one command that keeps the model, runtime, and LiteLLM alias aligned for a
workflow. The term "profile" is already used by Docker Compose for `gpu`,
`batch`, and `quality`, so using "model profile" would make docs and commands
ambiguous.

## Decision

Use **Serving Preset** for workflow-level model switching. A serving preset is a
data-driven binding of model, serving runtime, and gateway alias. Keep
`model select` as the low-level runtime command, use `preset apply` to write
generated active state, and use `config render` to translate that state into the
runtime `.env` values Docker Compose needs.

## Consequences

- Docker Compose profiles remain infrastructure lifecycle controls.
- Serving presets can grow by editing `models/presets.yaml` instead of adding
  bespoke CLI branches for every workflow.
- Runtime `.env` files remain local machine configuration; generated active
  selection state lives in `config/active/serving.yaml` and is gitignored.
- LiteLLM remains the client-facing gateway; Open WebUI reads aliases from
  LiteLLM and does not become the source of model configuration truth.
