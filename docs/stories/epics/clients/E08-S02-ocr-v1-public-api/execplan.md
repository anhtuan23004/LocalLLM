# Exec Plan

## Goal

Replace the one-image OCR extraction route with public OCR API v1 for image/PDF
classification and extraction while keeping model selection behind LiteLLM.

## Scope

In scope:

- Public v1 classify-segment and extract routes.
- PDF-to-image rendering.
- Strict LiteLLM structured-output requests.
- Unit, mocked integration, compose, and smoke validation.

Out of scope:

- Multipart upload.
- Direct provider adapters beyond LiteLLM.
- Runtime E2E without a configured vision model.

## Risk Classification

Risk flags:

- Public contracts.
- External systems.
- Existing behavior.
- Weak proof for live model runtime.

Hard gates:

- External provider behavior.

## Work Phases

1. Refactor OCR client modules.
2. Add strict schema and LiteLLM boundary.
3. Add unit and mocked integration tests.
4. Update docs, story evidence, and test matrix.
5. Run static validation.

## Stop Conditions

Pause if strict structured output cannot be supported by the selected LiteLLM
runtime model or if runtime proof needs to weaken validation requirements.
