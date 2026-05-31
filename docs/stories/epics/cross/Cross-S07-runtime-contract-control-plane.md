# Cross-S07 Runtime Contract Control Plane

## Status

implemented

## Lane

normal

## Product Contract

Runtime/service facts must have one tracked source that the control plane reads
instead of duplicating service ids, ports, compose paths, model env keys,
gateway aliases, and image defaults across scripts. The `./llm-local` entrypoint
must remain stable while routing through a testable Python command layer. The
validation ladder must expose concrete commands, and tracked runtime image
defaults must be pinned.

## Relevant Product Docs

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/HARNESS.md`
- `docs/product/domains.md`
- `docs/TEST_MATRIX.md`

## Acceptance Criteria

- `config/runtime-catalog.yaml` records service ids, compose paths, container
  names, host ports, GPU policy, model env keys, LiteLLM model env keys,
  evaluation endpoints, runtime checks, and image defaults.
- `scripts/preflight.py`, `models/manage.py`, `models/presets.py`,
  `llm_local.validation`, and the `./llm-local` command layer read runtime facts
  from `llm_local.catalog`.
- `llm-local` is a thin Bash shim over `python -m llm_local.cli`.
- `scripts/smoke.sh` is a thin compatibility shim over the validation ladder.
- `config/validation-commands.yaml` defines validation command metadata.
- `Makefile` exposes `validate-quick`, `test-integration`, `test-platform`, and
  `release-check`; `validate` and `smoke` run the quick ladder.
- Tracked compose image expressions and `.env.example` files no longer use
  moving image tags for third-party runtime images.
- Image validation checks catalog defaults, `.env.example` values, and compose
  image expressions for catalog-backed services.
- Quick validation passes without requiring ignored local model weight files.

## Design Notes

- Commands: `./llm-local validate quick`, `./llm-local validate integration`,
  `./llm-local validate platform`, `./llm-local validate release`.
- Runtime catalog interface: `llm_local.catalog`.
- CLI seam: `llm-local` shell wrapper delegates to `llm_local.cli`.
- Validation seam: `scripts/smoke.sh` delegates to `llm_local.validation`.
- Model registry validation has `--metadata-only` for quick checks and strict
  file validation for release checks.
- Local ignored `.env` files remain machine-specific overrides and were not made
  the source of truth.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Python compile checks for `llm_local`, preflight, model, and preset modules; Bash syntax for entrypoint shims. |
| Integration | `./llm-local validate quick` passes. |
| E2E | Not required; no user-visible browser flow changed. |
| Platform | Not required for the static control-plane change; `test-platform` is now defined for prepared runtime hosts. |
| Release | `release-check` is defined but requires a prepared GPU/runtime host and local model files. |

## Harness Delta

- Implemented validation ladder target alignment through
  `config/validation-commands.yaml` and Makefile targets.
- Implemented release gate naming through `make release-check`.
- Kept evidence freshness policy as a separate proposed backlog item.

## Evidence

2026-05-28, local workspace:

```text
$ ./llm-local validate quick
Results: 34 passed, 0 failed
```

Additional checks run:

```text
$ ./llm-local help
exited 0 and displayed the Python-routed command surface

$ ./llm-local validate images
Results: 1 passed, 0 failed
Validated catalog image defaults, matching `.env.example` values, and compose
image expressions.

$ make validate-quick
Results: 34 passed, 0 failed

$ make test-integration
Results: 20 passed, 0 failed

$ ./llm-local smoke
Results: 34 passed, 0 failed

$ ./llm-local validate list
listed validate-quick, test-integration, test-platform, and release-check

$ ./llm-local model validate --metadata-only
[+] All models validated successfully.

$ ./llm-local preset apply chat-small --dry-run --render
exited 0 and rendered OLLAMA_LITELLM_MODEL from catalog-backed preset metadata

$ python3 -m py_compile llm_local/*.py scripts/preflight.py models/manage.py models/presets.py models/validate_registry.py
exited 0
```
