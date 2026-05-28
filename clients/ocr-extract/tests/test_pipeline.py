import pytest

from src.documents import LoadedDocument, PageImage
from src.pipeline import OcrPipeline, normalize_classification_response, normalize_extracted_data
from src.schemas import ClassifySegmentResponse, ExtractRequest, ExtractionGroupSchema


def test_unknown_document_is_ignored_unless_schema_allows_unknown():
    response = ClassifySegmentResponse.model_validate(
        {
            "documents": [
                {
                    "document_code": "unknown",
                    "group_name": "Other",
                    "document_name": "Other",
                    "page_ranges": [[1, 1]],
                    "page_order": [1],
                    "duplicate_pages": [],
                }
            ]
        }
    )

    normalized = normalize_classification_response(
        response,
        allowed_groups={"invoice": "Invoice"},
        page_count=1,
    )

    assert normalized.documents == []


def test_normalize_extracted_data_fills_missing_values_with_null():
    group = ExtractionGroupSchema.model_validate(
        {
            "group_code": "invoice",
            "group_name": "Invoice",
            "group_description": "Invoice documents",
            "fields": [
                {
                    "field_key": "invoice_number",
                    "data_type": "string",
                    "nullable": False,
                },
                {
                    "field_key": "total_amount",
                    "data_type": "number",
                },
            ],
        }
    )

    extracted = normalize_extracted_data(group, {"invoice_number": "INV-001"})

    assert extracted == {"invoice_number": "INV-001", "total_amount": None}


def test_normalize_extracted_data_rejects_extra_keys():
    group = ExtractionGroupSchema.model_validate(
        {
            "group_code": "invoice",
            "group_name": "Invoice",
            "group_description": "Invoice documents",
            "fields": [{"field_key": "invoice_number", "data_type": "string"}],
        }
    )

    with pytest.raises(ValueError, match="unexpected keys"):
        normalize_extracted_data(group, {"invoice_number": "INV-001", "extra": "bad"})


def test_page_order_must_match_page_ranges():
    response = ClassifySegmentResponse.model_validate(
        {
            "documents": [
                {
                    "document_code": "invoice",
                    "group_name": "Invoice",
                    "document_name": "Invoice",
                    "page_ranges": [[1, 2]],
                    "page_order": [1],
                    "duplicate_pages": [],
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="page_order must match"):
        normalize_classification_response(
            response,
            allowed_groups={"invoice": "Invoice"},
            page_count=2,
        )


class FakeVisionModelClient:
    def __init__(self):
        self.calls = []

    async def complete_json(self, *, prompt, pages, response_format):
        self.calls.append((prompt, pages, response_format))
        name = response_format["json_schema"]["name"]
        if name == "ocr_v1_classify_segment":
            return {
                "documents": [
                    {
                        "document_code": "invoice",
                        "group_name": "Invoice",
                        "document_name": "Invoice",
                        "page_ranges": [[1, 2]],
                        "page_order": [1, 2],
                        "duplicate_pages": [],
                    }
                ]
            }
        return {"invoice_number": "INV-001"}


def test_extract_pipeline_classifies_then_extracts_rendered_pages(monkeypatch):
    import asyncio
    import src.pipeline as pipeline

    loaded_document = LoadedDocument(
        file_name="file.pdf",
        mime_type="application/pdf",
        pages=[
            PageImage(page_number=1, content=b"page1", mime_type="image/png"),
            PageImage(page_number=2, content=b"page2", mime_type="image/png"),
        ],
    )

    async def fake_load_document(file_url):
        return loaded_document

    fake_model = FakeVisionModelClient()
    monkeypatch.setattr(pipeline, "load_document", fake_load_document)
    request = ExtractRequest.model_validate(
        {
            "file_url": "https://example.com/file.pdf",
            "extraction_schemas": [
                {
                    "group_code": "invoice",
                    "group_name": "Invoice",
                    "group_description": "Invoice documents",
                    "fields": [
                        {"field_key": "invoice_number", "data_type": "string"},
                        {"field_key": "total_amount", "data_type": "number"},
                    ],
                }
            ],
        }
    )

    response = asyncio.run(OcrPipeline(fake_model).extract(request))

    assert response.documents[0].page_order == [1, 2]
    assert response.documents[0].extracted_data == {
        "invoice_number": "INV-001",
        "total_amount": None,
    }
    assert [len(call[1]) for call in fake_model.calls] == [2, 2]
