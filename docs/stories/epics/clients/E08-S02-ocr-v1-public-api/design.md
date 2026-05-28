# Design

## Domain Model

The public contract uses Gemini-OCR v3-style group schemas. A group has
`group_code`, `group_name`, `group_description`, and optional `variants`.
Extraction groups add `fields`; non-`unknown` groups require fields.

## Application Flow

`classify-segment` downloads the file, renders PDF pages to PNG when needed,
then asks the configured LiteLLM Gateway Alias for strict JSON matching the
classification schema.

`extract` runs classification first, selects page images by `page_order`, then
extracts each document with a per-group strict schema and wraps the result in
the v1 response envelope.

## Interface Contract

Public requests accept `file_url` and `extraction_schemas` only. They do not
accept `model_name`, `api_key`, `temperature`, `thinking_budget`, or other
provider-specific fields.

Responses use `documents[]`. Classification documents include
`page_ranges`, `page_order`, and `duplicate_pages`; each `page_ranges` item is
exactly `[start_page, end_page]`. Extraction documents include `page_order`,
`duplicate_pages`, and `extracted_data`. Field schemas may use `nullable: false`
to disallow null output. `required: false` is rejected because strict structured
output requires every key to remain required.

`file_url` download targets must resolve to public internet addresses. The
service validates the initial URL and each redirect target before fetching.
Upstream 5xx download responses return 502 and download timeouts return 504.

## Data Model

No persistent data model changes.

## UI / Platform Impact

Docker Compose remains the platform surface. `LITELLM_MODEL` is required at runtime
and represents the LiteLLM Gateway Alias used by the client.

## Observability

Existing container health and smoke checks remain the validation surface. Runtime
model failures return 502; missing `LITELLM_MODEL` returns a configuration error.
Download SSRF rejections return 400 before model work starts.

## Alternatives Considered

1. Sending raw PDFs directly to the model was rejected because model/provider PDF
   support would leak into the public client contract.
2. JSON-mode fallback was rejected because this API requires strict structured
   output.
