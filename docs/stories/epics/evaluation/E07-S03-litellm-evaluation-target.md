# E07-S03 LiteLLM Evaluation Target

## Status

implemented

## Lane

normal

## Product Contract

Evaluation can send benchmark traffic through the LiteLLM gateway with:

```bash
./llm-local eval run --target litellm --model <alias>
make benchmark-litellm MODEL=<alias>
```

Benchmark output continues to record the model name supplied by the caller,
which is the LiteLLM alias for gateway runs.

## Relevant Product Docs

- `docs/product/domains.md` (Evaluation).
- `README.md` (Run Evaluation).
- `docs/stories/initiatives/litellm-gateway.md`.

## Acceptance Criteria

- `llm-local` accepts `--target litellm`.
- LiteLLM evaluation uses endpoint `http://litellm:4000` from the evaluation
  container on `llm-net`.
- LiteLLM evaluation passes an optional bearer token; gateway runs default to
  `LITELLM_MASTER_KEY` or `sk-local-litellm`.
- `evaluation/scripts/run_benchmark.py` accepts optional `--api-key`.
- `make benchmark-litellm MODEL=<alias>` exists.
- Existing direct benchmark targets remain present.

## Design Notes

- The benchmark script keeps its existing OpenAI-compatible request path and
  adds only an optional `Authorization: Bearer <token>` header.
- `benchmark-ollama` and `benchmark-vllm` keep their `MODEL=llama3` default.
- `benchmark-litellm` defaults to `MODEL=local-ollama`.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `bash -n llm-local`; `python3 -m py_compile evaluation/scripts/run_benchmark.py` |
| Integration | `make validate-compose`; `./llm-local smoke` |
| E2E | Runtime benchmark JSON deferred until a backend model is available behind LiteLLM |
| Platform | n/a |
| Release | n/a |

## Harness Delta

- Added this story packet.
- Added `E07-S03` to `docs/TEST_MATRIX.md`.
- Updated the LiteLLM initiative and story backlog link.

## Evidence

```bash
$ bash -n llm-local
# exits 0

$ python3 -m py_compile evaluation/scripts/run_benchmark.py
# exits 0

$ make help | rg 'benchmark-litellm|litellm-up'
# lists litellm-up and benchmark-litellm

$ ./llm-local eval run --target invalid
# errors with the supported target list including litellm

$ make validate-compose
# exits 0

$ ./llm-local smoke
# exits 0 with Results: 20 passed, 0 failed
```

Runtime benchmark JSON remains deferred until Ollama or another backend is
running behind LiteLLM with the requested alias.
