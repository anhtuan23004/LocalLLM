# Harness

The project goal is to provide a reusable operating harness that lets humans and
agents turn product intent into safe, validated work.

The app is what users touch. The harness is what agents touch.

## Current Repository State

LLM-Local has product-specific infrastructure for serving, training,
evaluation, observation, and model management. The harness is no longer empty:
`docs/product/`, `docs/ARCHITECTURE.md`, `docs/stories/backlog.md`, and
`docs/TEST_MATRIX.md` contain the current LLM-Local contract.

Validation proof is tracked per story. Test matrix rows marked `implemented`
must point to story packets that capture evidence from real commands, reports,
logs, or screenshots. Rows without recorded evidence should stay `planned`.

## Mental Model

```text
------------------+
| Human intent    |
+------------------+
         |
         v
+------------------+
| Feature intake   |
+------------------+
         |
         v
+------------------+
| Story packet     |
+------------------+
         |
         v
+------------------+
| Agent work loop  |
+------------------+
         |
         v
+------------------+
| Product delta    |
+------------------+
         |
         v
+------------------+
| Validation proof |
+------------------+
         |
         v
+------------------+
| Harness delta    |
+------------------+
         |
         v
+------------------+
| Next intent      |
+------------------+
```

Every task has two possible outputs:

1. Product delta: app code, tests, API shape, data model, or product docs.
2. Harness delta: docs, templates, validation expectations, backlog items, or
   decision records that make the next task easier.

## Harness v0 Scope

A fresh Harness v0 install includes:

- Agent entrypoint.
- Empty product documentation structure.
- Feature intake and risk lanes.
- Story templates.
- Decision log template.
- Validation report template.
- Test matrix placeholder.
- Harness growth backlog.

Harness v0 deliberately excludes:

- A project-specific `SPEC.md`.
- Pre-sliced product domains.
- A locked application stack.
- App source scaffolding.
- Package scripts.
- Test runner config.
- CI workflows.
- Database migrations or infrastructure.

Those should arrive only when a selected story needs them. In this repository,
LLM-Local infrastructure has already been introduced, but new implementation
areas should still enter through feature intake and story packets.

## Source Hierarchy

```text
User-provided spec or prompt
  input material for first buildout or future changes

docs/product/*
  current product contract derived from accepted input

docs/stories/*
  story-sized work packets and historical evidence

docs/TEST_MATRIX.md
  behavior-to-proof control panel

docs/decisions/*
  why the contract changed
```

Before a behavior is implemented, product docs describe intent. After a
behavior is implemented, product docs plus executable tests become the living
contract.

## Spec Lifecycle

A fresh Harness v0 starts without a tracked project spec. This repository has
already completed an LLM-Local intake pass. When the human provides a new
specification or initiative, treat it as input material, not as a permanent
operating manual. Use it to populate product docs, story packets, architecture
decisions, and validation expectations during that buildout.

After the specification has been decomposed, do not keep extending it as the
living product plan. Ongoing work should update the smaller product docs,
stories, test matrix, and decision records.

Ongoing work should enter the harness as one of these input types:

- New spec: a project specification that needs to become product docs and
  initial story candidates.
- Spec slice: a selected behavior from the provided spec.
- Change request: a bounded behavior change, bug fix, or product refinement.
- New initiative: a larger product area that needs multiple stories.
- Maintenance request: dependency, architecture, performance, security, or
  operational work.
- Harness improvement: a process, template, proof, or agent-instruction change.

The spec-to-work loop is:

```text
human intent or supplied spec
  -> classify input type
  -> update or create product contract
  -> create story packet or initiative notes when needed
  -> define validation proof
  -> implement or document the blocker
  -> update product docs, stories, test matrix, and decisions
  -> capture harness friction
```

Large product areas should use scoped initiative notes instead of a second
monolithic specification. An initiative should explain the goal, affected
product docs, candidate stories, validation shape, open decisions, and exit
criteria. If initiative work becomes a repeated pattern, add a template or
proposal to `docs/HARNESS_BACKLOG.md`.

## Growth Rule

The harness grows from friction.

When an agent is confused, repeats manual reasoning, needs a new validation
command, discovers a missing rule, or sees a recurring failure pattern, it must
either improve the harness directly or add a proposal to `HARNESS_BACKLOG.md`.

## Validation Ladder

The executable validation command registry lives in
`config/validation-commands.yaml`. The stable top-level commands are:

```text
make validate-quick
  static validation: runtime catalog, compose configs, metadata-only registry
  checks, script syntax, dashboard JSON, Makefile help, and pinned image
  defaults

make test-integration
  integration validation for compose/config and product-contract checks that do
  not require live LLM services

make test-platform
  live host validation for Docker network, running containers, and host
  endpoints; use only on a prepared runtime host

make release-check
  release validation on a prepared GPU/runtime host; includes strict model
  registry file checks and runtime checks
```

`make validate` and `make smoke` run `make validate-quick`. Agents must not
claim a command passes until it has been run in the current workspace.
