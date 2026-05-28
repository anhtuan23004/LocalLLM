from fastapi.testclient import TestClient

import src.app as app_module
from src.schemas import ClassifySegmentResponse


class FakePipeline:
    async def classify_segment(self, request):
        return ClassifySegmentResponse.model_validate(
            {
                "documents": [
                    {
                        "document_code": request.extraction_schemas[0].group_code,
                        "group_name": request.extraction_schemas[0].group_name,
                        "document_name": request.extraction_schemas[0].group_name,
                        "page_ranges": [[1, 1]],
                        "page_order": [1],
                        "duplicate_pages": [],
                    }
                ]
            }
        )


def test_v1_classify_segment_route(monkeypatch):
    monkeypatch.setattr(app_module, "OcrPipeline", FakePipeline)
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/ocr/classify-segment",
        json={
            "file_url": "https://example.com/file.png",
            "extraction_schemas": [
                {
                    "group_code": "invoice",
                    "group_name": "Invoice",
                    "group_description": "Invoice documents",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["documents"][0]["document_code"] == "invoice"


def test_v3_extract_route_removed():
    client = TestClient(app_module.app)

    response = client.post("/api/v3/ocr/extract", json={})

    assert response.status_code == 404
