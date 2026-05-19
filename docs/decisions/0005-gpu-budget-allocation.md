# 0005 — GPU Budget and Allocation Policy

## Status

accepted

## Context

Multiple services claim GPU access simultaneously:

- **vLLM**: `device_ids: ['0']`, `gpu-memory-utilization: 0.9`
- **Ollama**: `capabilities: ["gpu"]` (claims all GPUs)
- **Unsloth**: `count: all` (claims all GPUs)

On a single-GPU workstation, running vLLM + Ollama + Unsloth together causes
VRAM contention and OOM kills. Even on multi-GPU, overlapping `count: all`
claims create unpredictable allocation.

## Decision

### Single-GPU systems

Only one GPU-heavy service runs at a time. Priority order:

1. **Serving** (vLLM or Ollama, not both) — primary use case
2. **Training** (Unsloth) — requires stopping serving first

Ollama is lighter and can coexist with vLLM only if `VLLM_GPU_MEMORY_UTILIZATION`
is reduced (e.g., 0.5).

### Multi-GPU systems (2+ GPUs)

| GPU | Assigned To | Rationale |
|-----|-------------|-----------|
| 0   | vLLM        | Production serving, fixed allocation |
| 1   | Training / Ollama | Experimentation, flexible |

Enforce via:
- vLLM: `CUDA_VISIBLE_DEVICES=0` + `device_ids: ['0']`
- Unsloth: add `CUDA_VISIBLE_DEVICES=1` to compose environment
- Ollama: add `device_ids: ['1']` to compose deploy config

### Rules

- Never run `count: all` on more than one service simultaneously.
- Do not use floating `latest` tags for GPU runtime images. Pin image tags to
  a CUDA generation compatible with the host driver; otherwise Docker may pull
  an image that requires a newer CUDA runtime than the installed NVIDIA driver
  supports.
- Older CUDA-compatible tags may not support newer model architectures. When
  raising `VLLM_IMAGE_TAG` for model support, verify the host driver supports
  that image's CUDA requirement before changing the default.
- `make smoke` remains a lightweight configuration regression guard and does
  not enforce live GPU allocation.
- `Cross-S03` GPU pre-check should warn when multiple GPU-heavy services are
  running or when compose settings would claim overlapping devices.
- The model registry currently records serving intent through `serving_target`.
  Future registry fields may record preferred GPU placement, but the registry
  does not currently decide runtime GPU allocation.

## Consequences

- Single-GPU users must stop serving before training (acceptable for local dev).
- Multi-GPU users get concurrent serving + training without conflicts.
- Future: `Cross-S03` pre-check script should read this policy and enforce it.
