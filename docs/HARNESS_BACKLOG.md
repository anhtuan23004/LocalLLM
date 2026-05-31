# Harness Backlog

Use this file when an agent discovers a missing harness capability but should
not change the operating model immediately.

## Template

```md
## Missing Harness Capability

### Title

Short name.

### Discovered While

Task or story that exposed the gap.

### Current Pain

What was hard, repeated, ambiguous, or unsafe?

### Suggested Improvement

What should be added or changed?

### Risk

Tiny, normal, or high-risk.

### Status

proposed | accepted | implemented | rejected
```

## Items

## Missing Harness Capability

### Title

Validation ladder target alignment.

### Discovered While

Reconciling follow-up validation status.

### Current Pain

`docs/HARNESS.md` describes a future ladder with names such as
`validate:quick`, `test:integration`, and `test:release`, while the repository
currently exposes concrete targets such as `make validate` and `make smoke`.
Agents need a clear mapping from current commands to the future ladder before
adding more gates.

### Suggested Improvement

Add a small validation-command registry that names the current command, intended
future ladder level, required environment, expected runtime, and whether the
command is allowed in CI.

### Risk

tiny

### Status

implemented by `docs/stories/epics/cross/Cross-S07-runtime-contract-control-plane.md`

## Missing Harness Capability

### Title

Evidence freshness policy.

### Discovered While

Refreshing backlog status from `docs/TEST_MATRIX.md`.

### Current Pain

Implemented matrix rows link to story evidence, but the harness does not define
when evidence becomes stale, how to record host/date/version context, or when a
previously implemented row should be revalidated after infrastructure changes.

### Suggested Improvement

Extend story evidence guidance with required freshness metadata: validation
date, host/runtime context when relevant, command version or image tag, and a
rule for marking rows `changed` when underlying validation assumptions drift.

### Risk

normal

### Status

implemented by `docs/stories/epics/cross/Cross-S07-runtime-contract-control-plane.md`

## Missing Harness Capability

### Title

Release gate naming.

### Discovered While

Prioritizing the remaining planned vLLM story and reviewing matrix proof layers.

### Current Pain

The matrix has a Release proof layer, but the repository has no named release
gate command. This makes it unclear what future agents should run before a
release-level claim, especially for GPU/runtime checks that cannot run in
ordinary CI.

### Suggested Improvement

Define release gate names such as `make release-check` or
`make validate-release`, including which parts run locally, in CI, and on a
prepared GPU host.

### Risk

normal

### Status

proposed
