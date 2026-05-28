# E08-S01 OCR Extract Client

## Status

changed

## Lane

normal

## Product Contract

OCR Extract runs as a Docker Compose client service on `llm-net` and exposes a
Gemini-OCR-like `POST /api/v3/ocr/extract` endpoint for one image at a time. It
downloads a caller-provided image URL, sends the image and extraction schema to
LiteLLM through a configured gateway alias, validates the model JSON response,
and returns a V3-style `documents` payload.

This contract was superseded by E08-S02, which replaces the public route with
OCR API v1 classify-segment and extract endpoints that support image and PDF
inputs through strict LiteLLM structured output.

OCR Extract is a client of the LiteLLM gateway. It does not load model weights
and does not replace serving runtimes.

## Relevant Product Docs

- `docs/product/domains.md` (client service contract).
- `docs/ARCHITECTURE.md` (topology).
- `CONTEXT.md` (Client Service term).
- `clients/ocr-extract/README.md`.

## Acceptance Criteria

- `clients/ocr-extract/docker-compose.yml` defines an OCR Extract service on
  `llm-net`.
- The service exposes host port `18092` by default and container port `8092`.
- `GET /health` reports service health.
- `POST /api/v3/ocr/extract` accepts `file_url` and `extraction_schemas`.
- The service supports one image per request and rejects unsupported content
  types.
- The service calls LiteLLM at `LITELLM_BASE_URL` using `LITELLM_MODEL`, default
  `local-ollama`.
- The service validates that model output is JSON matching `{documents: [...]}`.
- `./llm-local ocr-extract up` and `./llm-local ocr-extract down` manage the
  client.
- Static validation includes the OCR Extract compose file and Python syntax.

## Design Notes

- API: `POST /api/v3/ocr/extract`.
- Input source: `file_url` only for this first slice.
- Supported MIME types: `image/png`, `image/jpeg`, `image/jpg`, `image/webp`.
- Output page metadata is fixed to `page_order: [1]` because this story handles
  one image, not PDF segmentation.
- PDF and multi-page classification/segmentation remain out of scope.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python3 -m py_compile clients/ocr-extract/src/app.py`; `bash -n llm-local`; `bash -n scripts/smoke.sh` |
| Integration | `docker compose -f clients/ocr-extract/docker-compose.yml config`; `make validate-compose`; `./llm-local smoke` |
| E2E | Runtime request through LiteLLM deferred until a vision model is active behind `local-ollama` |
| Platform | Host port conflict checked through startup guardrails |
| Release | n/a |

## Harness Delta

- Added this story packet.
- Added `E08-S01` to `docs/TEST_MATRIX.md`.
- Added OCR Extract to product domain docs, `llm-local`, Makefile, preflight,
  and smoke validation.

## Evidence

```bash
$ docker compose -f clients/ocr-extract/docker-compose.yml config
# exits 0 and resolves OCR Extract on llm-net with host port 18092.

$ python3 -m py_compile clients/ocr-extract/src/app.py
# exits 0.

$ bash -n llm-local
# exits 0.

$ bash -n scripts/smoke.sh
# exits 0.

$ make validate-compose
# exits 0 and includes clients/ocr-extract/docker-compose.yml.

$ ./llm-local smoke
# exits 0 with Results: 29 passed, 0 failed.
```
