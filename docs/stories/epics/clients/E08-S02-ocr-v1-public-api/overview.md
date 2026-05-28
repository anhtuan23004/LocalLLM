# Overview

## Current Behavior

OCR Extract previously exposed a one-image `/api/v3/ocr/extract` route that
accepted public model override fields and used a LiteLLM alias default.

## Target Behavior

OCR Extract exposes public API v1:

- `POST /api/v1/ocr/classify-segment`
- `POST /api/v1/ocr/extract`

The service accepts image or PDF `file_url`, rejects private/reserved download
destinations before and after redirects, renders PDF pages to images internally,
hides model selection from callers, requires `LITELLM_MODEL`, and sends strict
structured output requests through LiteLLM.

## Affected Users

- Developers calling OCR Extract as a local document-intelligence client.

## Affected Product Docs

- `docs/product/domains.md`
- `clients/ocr-extract/README.md`

## Non-Goals

- Multipart upload.
- Direct Gemini SDK adapter.
- PDF batching beyond the configured page limit.
- Runtime E2E proof without a configured vision model behind LiteLLM.
