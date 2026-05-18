# Test Matrix

This file maps product behavior to proof.

LLM-Local behavior has been defined from the current repository, but proof has
not been recorded yet. Do not mark a row implemented until tests or validation
evidence exist.

## Status Values

| Status | Meaning |
| --- | --- |
| planned | Accepted as intended behavior, not implemented |
| in_progress | Actively being built |
| implemented | Implemented and proof exists |
| changed | Contract changed after earlier implementation |
| retired | No longer part of the product contract |

## Matrix

| Story | Contract | Unit | Integration | E2E | Platform | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E01-S01 | Ollama serves chat completions on llm-net | no | no | no | no | planned | none |
| E01-S02 | Qwen-VL serves OpenAI-compat API via vLLM | no | no | no | no | planned | none |
| E02-S01 | Unsloth Jupyter accessible with GPU | no | no | no | no | planned | none |
| E03-S01 | Benchmark produces valid JSON with latency stats | no | no | no | no | planned | none |
| E04-S01 | Observation produces CSV summary + latency chart | no | no | no | no | planned | none |
| E05-S01 | download_model.py fetches model to correct path | no | no | no | no | planned | none |
| Cross-S01 | All services reachable on llm-net | no | no | no | no | planned | none |
| Cross-S04 | Compose configuration matches product contracts | n/a | yes | no | no | implemented | docs/stories/epics/cross/Cross-S04-compose-contract-drift.md |

## Evidence Rules

- Unit proof covers pure domain and application rules.
- Integration proof covers backend enforcement, data integrity, provider
  behavior, jobs, or service contracts.
- E2E proof covers user-visible browser flows.
- Platform proof covers only shell, deployment, mobile, desktop, or runtime
  behavior that cannot be proven in lower layers.
- A story can be implemented without every proof column if the story packet
  explains why.
