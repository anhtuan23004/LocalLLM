# Validation

## Proof Strategy

Use deterministic tests for request validation, strict schema construction, PDF
rendering, pipeline normalization, and mocked LiteLLM payloads. Static checks
prove compose/script compatibility. Runtime E2E stays conditional on a vision
model behind `LITELLM_MODEL`.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Pydantic validation, unknown policy, strict schema builders, field null filling, PDF page rendering |
| Integration | Mocked LiteLLM payload and endpoint/pipeline behavior |
| E2E | Deferred until a strict-output vision model is configured behind LiteLLM |
| Platform | Compose config and smoke checks |
| Performance | PDF page count and file size limits |
| Logs/Audit | n/a |

## Fixtures

- In-memory one-page and two-page PDFs generated with PyMuPDF.
- Mocked LiteLLM chat completion response.

## Commands

```text
uv run --with fastapi==0.115.6 --with httpx==0.28.1 --with pydantic==2.10.4 --with 'PyMuPDF>=1.23.0' --with 'pytest>=8.0.0' python -m pytest clients/ocr-extract/tests
python3 -m py_compile clients/ocr-extract/src/*.py
docker compose -f clients/ocr-extract/docker-compose.yml config
bash -n llm-local
bash -n scripts/smoke.sh
make validate-compose
./llm-local smoke
```

## Acceptance Evidence

```text
$ uv run --with fastapi==0.115.6 --with httpx==0.28.1 --with pydantic==2.10.4 --with 'PyMuPDF>=1.23.0' --with 'pytest>=8.0.0' python -m pytest clients/ocr-extract/tests
# exits 0; 18 passed.

$ python3 -m py_compile clients/ocr-extract/src/*.py
# exits 0.

$ docker compose -f clients/ocr-extract/docker-compose.yml config
# exits 0 and resolves OCR Extract on llm-net with LITELLM_MODEL env wiring.

$ bash -n llm-local
# exits 0.

$ bash -n scripts/smoke.sh
# exits 0.

$ make validate-compose
# exits 0; all compose configs valid.

$ ./llm-local smoke
# exits 0; Results: 29 passed, 0 failed.
```
