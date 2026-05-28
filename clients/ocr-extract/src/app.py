from fastapi import FastAPI

from .pipeline import OcrPipeline
from .schemas import (
    ClassifySegmentRequest,
    ClassifySegmentResponse,
    ExtractRequest,
    ExtractResponse,
)


app = FastAPI(title="LLM-Local OCR Extract Client", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "ocr-extract"}


@app.post(
    "/api/v1/ocr/classify-segment",
    response_model=ClassifySegmentResponse,
    response_model_exclude_none=True,
)
async def classify_segment(request: ClassifySegmentRequest) -> ClassifySegmentResponse:
    return await OcrPipeline().classify_segment(request)


@app.post(
    "/api/v1/ocr/extract",
    response_model=ExtractResponse,
    response_model_exclude_none=True,
)
async def extract(request: ExtractRequest) -> ExtractResponse:
    return await OcrPipeline().extract(request)
