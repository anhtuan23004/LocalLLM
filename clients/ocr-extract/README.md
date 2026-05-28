# OCR Extract Client

`ocr-extract` is a local Client Service for Gemini-OCR-like document
classification and extraction. It exposes public API v1 routes, renders PDF
pages to images internally, and calls the LiteLLM gateway with strict structured
output.

## Scope

- Endpoints:
  - `POST /api/v1/ocr/classify-segment`
  - `POST /api/v1/ocr/extract`
- Input: one HTTP/HTTPS `file_url` pointing to `image/png`, `image/jpeg`,
  `image/webp`, or `application/pdf`.
- Model route: required `LITELLM_MODEL` LiteLLM Gateway Alias.
- PDF handling: render pages to PNG before model calls.
- Structured output: requires `response_format.type=json_schema` with
  `strict=true`; no JSON-mode or prompt-only fallback.
- No multipart upload, direct Gemini SDK calls, or public model override fields.

## Run

```bash
cp clients/ocr-extract/.env.example clients/ocr-extract/.env
# Set LITELLM_MODEL in clients/ocr-extract/.env, for example LITELLM_MODEL=local-vllm
./llm-local serve litellm up
./llm-local ocr-extract up
```

The API is available at `http://localhost:18092`.

## Classify And Segment

```bash
curl -X POST "http://localhost:18092/api/v1/ocr/classify-segment" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://example.com/claim-file.pdf",
    "extraction_schemas": [
      {
        "group_code": "invoice",
        "group_name": "Invoice",
        "group_description": "A supplier invoice or payment request.",
        "variants": [
          {"name": "VAT invoice"},
          {"name": "Sales invoice"}
        ]
      },
      {
        "group_code": "unknown",
        "group_name": "Other",
        "group_description": "Readable documents outside known groups.",
        "variants": []
      }
    ]
  }'
```

Response:

```json
{
  "documents": [
    {
      "document_code": "invoice",
      "group_name": "Invoice",
      "document_name": "VAT invoice",
      "page_ranges": [[1, 1]],
      "page_order": [1],
      "duplicate_pages": []
    }
  ]
}
```

## Extract

`/extract` runs the full pipeline: classify/segment first, then extract each
document from its `page_order` images.

```bash
curl -X POST "http://localhost:18092/api/v1/ocr/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://example.com/claim-file.pdf",
    "extraction_schemas": [
      {
        "group_code": "invoice",
        "group_name": "Invoice",
        "group_description": "A supplier invoice or payment request.",
        "variants": [{"name": "VAT invoice"}],
        "fields": [
          {
            "field_key": "invoice_number",
            "data_type": "string",
            "field_name": "Invoice number"
          },
          {
            "field_key": "total_amount",
            "data_type": "number",
            "field_name": "Total amount"
          }
        ]
      }
    ]
  }'
```

Response:

```json
{
  "documents": [
    {
      "document_code": "invoice",
      "group_name": "Invoice",
      "document_name": "VAT invoice",
      "page_order": [1],
      "duplicate_pages": [],
      "extracted_data": {
        "invoice_number": "INV-001",
        "total_amount": 1000000
      }
    }
  ]
}
```

If a requested field is not visible, the key is still present with `null`.
Unknown documents are returned only when the caller includes a group with
`group_code: "unknown"`.

## Configuration

| Env var | Default | Meaning |
| --- | --- | --- |
| `LITELLM_MODEL` | none | Required LiteLLM Gateway Alias for OCR v1. |
| `LITELLM_BASE_URL` | `http://litellm:4000/v1` | LiteLLM OpenAI-compatible base URL. |
| `LITELLM_API_KEY` | `sk-local-litellm` | LiteLLM bearer token. |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Download and model request timeout. |
| `MAX_FILE_BYTES` | `52428800` | Maximum downloaded image/PDF size. |
| `MAX_PDF_PAGES` | `20` | Maximum PDF pages rendered in one request. |
| `PDF_RENDER_DPI` | `144` | PDF-to-PNG render resolution. |

Changing the model means changing `LITELLM_MODEL` or the LiteLLM alias behind it;
callers do not send model/provider fields in the public v1 API.
