# E05-S04 GGUF→Ollama Model Import

## Status

implemented

## Lane

tiny

## Product Contract

`models/convert.sh gguf2ollama <gguf-file>` creates an Ollama model from a GGUF
file. Generates a temporary Modelfile and runs `ollama create`.

## Relevant Product Docs

- `docs/product/domains.md` (Model Management)

## Acceptance Criteria

- `convert.sh gguf2ollama` validates ollama CLI is installed.
- Validates GGUF file exists before attempting import.
- `--name` overrides the default model name (derived from filename).
- Creates model via `ollama create` with a `FROM <path>` Modelfile.
- Cleans up temporary Modelfile after creation.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `convert.sh gguf2ollama /nonexistent.gguf` exits 1 with file-not-found error |
| Integration | With Ollama running, imports a GGUF and `ollama list` shows it |

## Evidence

```bash
$ ./models/convert.sh gguf2ollama /tmp/fake.gguf
ERROR: GGUF file not found: /tmp/fake.gguf

$ ./models/convert.sh gguf2ollama
ERROR: missing GGUF file.
Usage: ./models/convert.sh <hf2gguf|gguf2ollama> <path> [options]
```

Full import remains deferred until a GGUF file exists and the Ollama CLI/server
are available on the host.
