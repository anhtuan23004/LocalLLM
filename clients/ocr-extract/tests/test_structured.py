from src.schemas import ExtractionGroupSchema
from src.structured import extraction_response_schema, strict_response_format


def test_strict_response_format_uses_json_schema_strict():
    schema = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
    response_format = strict_response_format("sample", schema)

    assert response_format == {
        "type": "json_schema",
        "json_schema": {"name": "sample", "strict": True, "schema": schema},
    }


def test_extraction_schema_requires_all_fields_and_allows_null():
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
    assert {"type": "null"} in schema["properties"]["invoice_number"]["anyOf"]


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
