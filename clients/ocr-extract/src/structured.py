from typing import Any

from .schemas import DocumentGroupSchema, ExtractionGroupSchema, FieldSchema


def strict_response_format(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": schema,
        },
    }


def classify_response_schema(groups: list[DocumentGroupSchema]) -> dict[str, Any]:
    codes = [group.group_code for group in groups]
    group_names = [group.group_name for group in groups]
    document_item = {
        "type": "object",
        "properties": {
            "document_code": {"type": "string", "enum": codes},
            "group_name": {"type": "string", "enum": group_names},
            "document_name": {"type": "string"},
            "page_ranges": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "integer"}},
            },
            "page_order": {"type": "array", "items": {"type": "integer"}},
            "duplicate_pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "duplicate_of": {"type": "integer"},
                    },
                    "required": ["page", "duplicate_of"],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "document_code",
            "group_name",
            "document_name",
            "page_ranges",
            "page_order",
            "duplicate_pages",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "documents": {"type": "array", "items": document_item},
        },
        "required": ["documents"],
        "additionalProperties": False,
    }


def extraction_response_schema(group: ExtractionGroupSchema) -> dict[str, Any]:
    if group.group_code == "unknown" and not group.fields:
        return unknown_extraction_schema()

    properties = {field.field_key: field_schema(field) for field in group.fields}
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }


def field_schema(field: FieldSchema) -> dict[str, Any]:
    if field.data_type == "number":
        value_schema: dict[str, Any] = {"type": "number"}
    elif field.data_type == "boolean":
        value_schema = {"type": "boolean"}
    elif field.data_type == "array":
        child_properties = {
            child.field_key: field_schema(child)
            for child in (field.child_schema or [])
        }
        value_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": child_properties,
                "required": list(child_properties.keys()),
                "additionalProperties": False,
            },
        }
    else:
        value_schema = {"type": "string"}

    description = field.description or field.field_name
    if description:
        value_schema["description"] = description
    return {"anyOf": [value_schema, {"type": "null"}]}


def unknown_extraction_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field_key": {"type": "string"},
                        "field_name": {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["field_key", "field_name", "value"],
                    "additionalProperties": False,
                },
            },
            "tables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "table_key": {"type": "string"},
                        "table_name": {"type": "string"},
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "key": {"type": "string"},
                                    "label": {"type": "string"},
                                },
                                "required": ["key", "label"],
                                "additionalProperties": False,
                            },
                        },
                        "rows": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "cells": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "key": {"type": "string"},
                                                "value": {"type": "string"},
                                            },
                                            "required": ["key", "value"],
                                            "additionalProperties": False,
                                        },
                                    }
                                },
                                "required": ["cells"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["table_key", "table_name", "columns", "rows"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["fields", "tables"],
        "additionalProperties": False,
    }
