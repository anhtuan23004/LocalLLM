# SGLang Serving

SGLang serves Hugging Face-style models with OpenAI-compatible endpoints.

```bash
cp serving/sglang/.env.example serving/sglang/.env
cd serving/sglang && docker compose up -d
curl http://localhost:18030/health
```

Configure `SGLANG_MODEL_PATH` to point at a mounted model path such as
`/models/GLM-OCR`.
