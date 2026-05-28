from src.schemas import DocumentGroupSchema, ExtractionGroupSchema
from src.structured import classify_response_schema, extraction_response_schema, strict_response_format


def test_strict_response_format_uses_json_schema_strict():
    schema = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
    response_format = strict_response_format("sample", schema)

    assert response_format == {
        "type": "json_schema",
        "json_schema": {"name": "sample", "strict": True, "schema": schema},
    }


def test_classification_schema_restricts_page_ranges_to_pairs():
    group = DocumentGroupSchema.model_validate(
        {
            "group_code": "invoice",
            "group_name": "Invoice",
            "group_description": "Invoice documents",
        }
    )

    schema = classify_response_schema([group])
    page_range_item = (
        schema["properties"]["documents"]["items"]["properties"]["page_ranges"]["items"]
    )

    assert page_range_item["minItems"] == 2
    assert page_range_item["maxItems"] == 2
    assert page_range_item["items"] == {"type": "integer"}


def test_extraction_schema_requires_all_fields_and_respects_nullable():
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

    schema = extraction_response_schema(group)

    assert schema["required"] == ["invoice_number", "total_amount"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["invoice_number"] == {"type": "string"}
    assert {"type": "null"} in schema["properties"]["total_amount"]["anyOf"]


def test_unknown_schema_has_no_open_object_properties():
    group = ExtractionGroupSchema.model_validate(
        {
            "group_code": "unknown",
            "group_name": "Other",
            "group_description": "Other documents",
            "fields": [],
        }
    )

    schema = extraction_response_schema(group)

    assert_all_objects_closed(schema)


def assert_all_objects_closed(fragment):
    if isinstance(fragment, dict):
        if fragment.get("type") == "object":
            assert fragment.get("additionalProperties") is False
        for value in fragment.values():
            assert_all_objects_closed(value)
    elif isinstance(fragment, list):
        for value in fragment:
            assert_all_objects_closed(value)
