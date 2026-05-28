import pytest
from pydantic import ValidationError

from src.schemas import ClassifySegmentRequest, ExtractRequest


def test_public_requests_forbid_model_controls():
    with pytest.raises(ValidationError):
        ClassifySegmentRequest.model_validate(
            {
                "file_url": "https://example.com/file.pdf",
                "model_name": "local-vllm",
                "extraction_schemas": [
                    {
                        "group_code": "invoice",
                        "group_name": "Invoice",
                        "group_description": "Invoice documents",
                    }
                ],
            }
        )


def test_extract_requires_fields_for_non_unknown_groups():
    with pytest.raises(ValidationError):
        ExtractRequest.model_validate(
            {
                "file_url": "https://example.com/file.pdf",
                "extraction_schemas": [
                    {
                        "group_code": "invoice",
                        "group_name": "Invoice",
                        "group_description": "Invoice documents",
                        "fields": [],
                    }
                ],
            }
        )


def test_unknown_group_may_omit_fields():
    request = ExtractRequest.model_validate(
        {
            "file_url": "https://example.com/file.pdf",
            "extraction_schemas": [
                {
                    "group_code": "unknown",
                    "group_name": "Other",
                    "group_description": "Documents outside known groups",
                    "fields": [],
                }
            ],
        }
    )

    assert request.extraction_schemas[0].fields == []


def test_duplicate_group_codes_are_rejected():
    with pytest.raises(ValidationError):
        ClassifySegmentRequest.model_validate(
            {
                "file_url": "https://example.com/file.pdf",
                "extraction_schemas": [
                    {
                        "group_code": "invoice",
                        "group_name": "Invoice",
                        "group_description": "Invoice documents",
                    },
                    {
                        "group_code": "invoice",
                        "group_name": "Duplicate",
                        "group_description": "Duplicate invoice documents",
                    },
                ],
            }
        )


def test_required_false_fields_are_rejected_for_strict_output():
    with pytest.raises(ValidationError, match="required=False is not supported"):
        ExtractRequest.model_validate(
            {
                "file_url": "https://example.com/file.pdf",
                "extraction_schemas": [
                    {
                        "group_code": "invoice",
                        "group_name": "Invoice",
                        "group_description": "Invoice documents",
                        "fields": [
                            {
                                "field_key": "invoice_number",
                                "data_type": "string",
                                "required": False,
                            }
                        ],
                    }
                ],
            }
        )
