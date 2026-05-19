# E02-S01 Unsloth Jupyter Accessible With GPU

## Status

implemented

## Lane

normal

## Product Contract

The Unsloth training compose service starts on `llm-net`, exposes Jupyter Lab,
mounts shared `models/` and `datasets/`, and can load the training environment
with GPU access.

## Relevant Product Docs

- `docs/product/domains.md` (Training).
- `docs/ARCHITECTURE.md` (Topology and shared resources).
- `docs/decisions/0005-gpu-budget-allocation.md`.

## Acceptance Criteria

- `training/unsloth/docker-compose.yml` resolves successfully.
- `docker compose up -d` starts the `unsloth` service on the target GPU host.
- Jupyter is reachable on host port `8888`.
- The container can import `unsloth`.
- Shared `models/` and `datasets/` mounts are present.

## Design Notes

- Unsloth currently claims all GPUs. On a single-GPU workstation, stop serving
  workloads before starting training, per ADR 0005.
- This story validates environment load, not a full fine-tuning run.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | n/a |
| Integration | Compose resolves; container starts; `import unsloth` succeeds |
| E2E | n/a |
| Platform | Jupyter reachable on `localhost:8888` on target host |
| Release | n/a |

## Harness Delta

- Added this story packet and updated `docs/TEST_MATRIX.md`.

## Evidence

```bash
$ cd training/unsloth
$ docker compose config
# exits 0

$ docker compose up -d
# starts unsloth on the target GPU host

$ docker exec unsloth python -c "import unsloth; print('ok')"
ok

$ curl -I http://localhost:8888
# returns an HTTP response from Jupyter
```
