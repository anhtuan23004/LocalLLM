# Documentation Map

This directory holds the project harness and the current LLM-Local product
contract derived from repository intake.

## Main Files

- `HARNESS.md`: how humans and agents collaborate.
- `FEATURE_INTAKE.md`: how prompts become tiny, normal, or high-risk work.
- `ARCHITECTURE.md`: architecture discovery and boundary rules.
- `TEST_MATRIX.md`: living map of behavior to proof.
- `HARNESS_BACKLOG.md`: improvements discovered while working.
- `GLOSSARY.md`: shared terms.

## Folders

- `product/`: current LLM-Local product truth.
- `stories/`: feature packets and backlog.
- `stories/initiatives/`: larger multi-story initiatives before slicing.
- `decisions/`: durable decisions and tradeoffs.
- `templates/`: reusable spec-intake, story, decision, and validation formats.

## Current State

Harness v0 is active and LLM-Local infrastructure exists. These docs define how
the project should grow from here. Automated validation proof, CI, and a
top-level validation command contract do not exist yet.

## Documentation Architecture

```text
Human prompt / new spec / change request
              |
              v
      +------------------+
      | FEATURE_INTAKE   |
      | classify input   |
      | choose risk lane |
      +------------------+
              |
              v
   +-------------------------+
   | Product contract        |
   | docs/product/*          |
   | What must be true?      |
   +-------------------------+
              |
              v
   +-------------------------+
   | Architecture contract   |
   | ARCHITECTURE.md         |
   | Where does it fit?      |
   +-------------------------+
              |
              v
   +-------------------------+
   | Story work packet       |
   | docs/stories/*          |
   | What exact slice moves? |
   +-------------------------+
              |
              v
   +-------------------------+
   | Validation control      |
   | TEST_MATRIX.md          |
   | What proves it works?   |
   +-------------------------+
              |
              v
   +-------------------------+
   | Decision history        |
   | docs/decisions/*        |
   | Why was this chosen?    |
   +-------------------------+
              |
              v
   +-------------------------+
   | Harness improvement     |
   | HARNESS_BACKLOG.md      |
   | What should be easier   |
   | for the next agent?     |
   +-------------------------+
```

## How The Docs Work

The docs are not just notes. They are the control surface for future agent work.
Each file has one job, and the files form a loop from intent to proof.

### 1. Intent Enters Through Feature Intake

Every new prompt, spec, bug fix, infrastructure change, or harness improvement
starts at `FEATURE_INTAKE.md`.

Feature intake answers:

- What kind of input is this?
- Is it a new spec, spec slice, change request, maintenance task, or harness
  improvement?
- Which risk lane applies: tiny, normal, or high-risk?
- Which product docs, stories, validation rows, and decisions may need updates?

The goal is to prevent agents from jumping straight from a vague prompt into
code or compose changes.

### 2. Product Docs Hold Current Truth

`docs/product/` describes what LLM-Local is expected to do.

For this repo, the product contract currently covers:

- Serving through Ollama and vLLM.
- Training through Unsloth.
- Evaluation through benchmark scripts.
- Observation through metrics and charts.
- Model management through local model downloads.

When behavior changes, update product docs first or alongside the story. The
original prompt or spec is input material; `docs/product/` is the living truth.

### 3. Architecture Explains Boundaries

`ARCHITECTURE.md` explains how the product contract maps onto the repository.

For LLM-Local, the important boundaries are:

- Docker Compose stacks for each domain.
- The shared external `llm-net` network.
- Bind-mounted folders such as `models/`, `datasets/`,
  `evaluation/results/`, and `observation/dashboards/`.
- Python scripts that sit at the edge of services and files.

Before proposing implementation shape, agents should check this file so changes
fit the existing topology.

### 4. Stories Turn Truth Into Work

`docs/stories/` turns product intent into bounded work packets.

Use:

- `docs/templates/story.md` for normal story-sized work.
- `docs/templates/high-risk-story/` when the change has security, data,
  external provider, public contract, or multi-domain risk.
- `docs/stories/backlog.md` for candidate stories that are not selected yet.

A story should explain the target behavior, affected docs, acceptance criteria,
validation expectations, and evidence after work is verified.

### 5. Test Matrix Tracks Proof

`TEST_MATRIX.md` is the proof control panel.

It links each behavior or story to validation layers:

- Unit.
- Integration.
- E2E.
- Platform.
- Release.

A row should stay `planned` until real evidence exists. Evidence can be command
output, generated reports, logs, screenshots, or validation report files. Do
not mark behavior implemented just because code or compose files exist.

### 6. Decisions Preserve Why

`docs/decisions/` records durable choices and tradeoffs.

Add or update a decision when work changes:

- Architecture direction.
- Product scope.
- Validation requirements.
- Risk posture.
- A previously settled rule.

This keeps future agents from repeatedly reopening the same question.

### 7. Harness Backlog Captures Process Gaps

`HARNESS_BACKLOG.md` is for problems in the workflow itself.

Use it when an agent discovers missing process support, such as:

- A repeated validation step with no template.
- A recurring ambiguity in feature intake.
- A missing checklist for Docker/GPU work.
- A documentation pattern that should become reusable.

Product bugs and implementation gaps belong in `docs/stories/backlog.md`.
Harness process gaps belong in `HARNESS_BACKLOG.md`.

## Operating Logic

```text
1. Read current truth:
   README.md -> HARNESS.md -> FEATURE_INTAKE.md -> docs/product/*

2. Classify the request:
   input type + risk lane + affected docs

3. Pick the right work container:
   tiny patch, normal story, or high-risk story folder

4. Make or plan the product delta:
   compose, script, docs, contract, or operational change

5. Record proof:
   update TEST_MATRIX.md and story evidence after validation exists

6. Record why:
   add a decision when the choice affects future work

7. Improve the harness:
   update docs directly for small clarifications, or add a backlog item for
   larger process changes
```
