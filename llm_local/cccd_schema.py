"""Shared CCCD OCR prompt and JSON schema helpers."""

from __future__ import annotations

import json
from typing import Any, Literal

Side = Literal["front", "back"]

SYSTEM_PROMPT = (
    "You are a strict OCR-to-JSON transcriber for Vietnamese CCCD documents. "
    "Output exactly one minified JSON object and nothing else. "
    "Do not use markdown, code fences, comments, or explanations. "
    "Preserve visible text exactly as written; do not normalize dates, names, punctuation, or casing. "
    "Use null for any unreadable or missing value. "
    "Do not invent information. "
    "Keep only the keys specified in the schema and do not reorder the schema conceptually."
)

FRONT_FIELD_KEYS = [
    "id_number",
    "full_name",
    "date_of_birth",
    "gender",
    "nationality",
    "place_of_origin",
    "date_of_expiry",
    "place_of_residence",
]

BACK_FIELD_KEYS = [
    "special_mark",
    "back_date",
]

MRZ_FIELD_KEYS = [
    "country",
    "document_number",
    "document_number_checksum",
    "document_number_checksum_validate",
    "personal_number",
    "personal_number_checksum",
    "personal_number_checksum_validate",
    "dob",
    "dob_checksum",
    "dob_checksum_validate",
    "gender",
    "due_date",
    "due_date_checksum",
    "due_date_checksum_validate",
    "nationality",
    "checksum",
    "sur_name",
    "given_name",
]


def cccd_template(side: str) -> dict[str, Any]:
    if side == "front":
        return {
            "document_type": "cccd",
            "side": "front",
            "fields": {key: None for key in FRONT_FIELD_KEYS},
        }
    if side == "back":
        return {
            "document_type": "cccd",
            "side": "back",
            "fields": {
                "special_mark": None,
                "back_date": None,
                "mrz": {key: None for key in MRZ_FIELD_KEYS},
            },
        }
    raise ValueError(f"unknown CCCD side: {side}")


def schema_literal(side: str) -> str:
    return json.dumps(cccd_template(side), ensure_ascii=False, separators=(",", ":"))


def side_prompt(side: str) -> tuple[str, str]:
    if side == "front":
        label = "FRONT"
    elif side == "back":
        label = "BACK"
    else:
        raise ValueError(f"unknown CCCD side: {side}")

    return (
        SYSTEM_PROMPT,
        (
            "<image>\n"
            f"Extract the {label} side of the Vietnamese CCCD.\n"
            "Return JSON matching this exact schema:\n"
            f"{schema_literal(side)}\n"
            "Rules:\n"
            "- Keep every key exactly as written.\n"
            "- Use null for unreadable or absent values.\n"
            "- Do not add extra keys.\n"
            "- Do not normalize dates; keep the source format as seen."
        ),
    )


def nullable_string_schema() -> dict[str, Any]:
    return {"anyOf": [{"type": "string"}, {"type": "null"}]}


def response_schema(side: str) -> dict[str, Any]:
    if side == "front":
        fields = {key: nullable_string_schema() for key in FRONT_FIELD_KEYS}
        required_fields = FRONT_FIELD_KEYS
    elif side == "back":
        mrz = {key: nullable_string_schema() for key in MRZ_FIELD_KEYS}
        fields = {
            "special_mark": nullable_string_schema(),
            "back_date": nullable_string_schema(),
            "mrz": {
                "type": "object",
                "properties": mrz,
                "required": MRZ_FIELD_KEYS,
                "additionalProperties": False,
            },
        }
        required_fields = [*BACK_FIELD_KEYS, "mrz"]
    else:
        raise ValueError(f"unknown CCCD side: {side}")

    return {
        "type": "object",
        "properties": {
            "document_type": {"type": "string", "enum": ["cccd"]},
            "side": {"type": "string", "enum": [side]},
            "fields": {
                "type": "object",
                "properties": fields,
                "required": required_fields,
                "additionalProperties": False,
            },
        },
        "required": ["document_type", "side", "fields"],
        "additionalProperties": False,
    }


def response_format(side: str) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": f"cccd_{side}_extraction",
            "strict": True,
            "schema": response_schema(side),
        },
    }


def field_paths(side: str) -> list[str]:
    if side == "front":
        return [f"fields.{key}" for key in FRONT_FIELD_KEYS]
    if side == "back":
        return [f"fields.{key}" for key in BACK_FIELD_KEYS] + [f"fields.mrz.{key}" for key in MRZ_FIELD_KEYS]
    raise ValueError(f"unknown CCCD side: {side}")
