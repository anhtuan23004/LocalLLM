"""Shared CCCD comparison and normalization helpers."""

from __future__ import annotations

import unicodedata
from typing import Any

from .cccd_schema import cccd_template, field_paths


def normalize_cccd_value(value: Any) -> Any:
    if isinstance(value, str):
        normalized = unicodedata.normalize("NFKC", value).strip()
        normalized = " ".join(normalized.split())
        return normalized.casefold()
    if isinstance(value, dict):
        return {key: normalize_cccd_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_cccd_value(item) for item in value]
    return value


def compare_cccd_values(expected: Any, predicted: Any) -> bool:
    return normalize_cccd_value(expected) == normalize_cccd_value(predicted)


def get_path(payload: dict[str, Any], path: str) -> Any:
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def score_cccd_payload(expected: dict[str, Any], predicted: dict[str, Any], side: str) -> dict[str, Any]:
    matches = {}
    for path in field_paths(side):
        expected_value = get_path(expected, path)
        predicted_value = get_path(predicted, path)
        matches[path] = {
            "expected": expected_value,
            "predicted": predicted_value,
            "match": compare_cccd_values(expected_value, predicted_value),
        }
    matched = sum(1 for item in matches.values() if item["match"])
    total = len(matches)
    return {
        "exact_match": compare_cccd_values(expected, predicted),
        "field_matches": matches,
        "matched_fields": matched,
        "total_fields": total,
        "field_accuracy": matched / total if total else 0,
    }


def schema_errors(payload: dict[str, Any], side: str) -> list[str]:
    errors: list[str] = []
    template = cccd_template(side)

    def path_key(prefix: str, key: str) -> str:
        return f"{prefix}.{key}" if prefix else key

    def visit(expected: Any, actual: Any, path: str) -> None:
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                errors.append(f"{path or '$'} must be an object")
                return
            expected_keys = set(expected)
            actual_keys = set(actual)
            for key in sorted(expected_keys - actual_keys):
                errors.append(f"{path_key(path, key)} is missing")
            for key in sorted(actual_keys - expected_keys):
                errors.append(f"{path_key(path, key)} is not allowed")
            for key in expected_keys & actual_keys:
                visit(expected[key], actual[key], path_key(path, key))
            return
        if expected is None:
            if actual is not None and not isinstance(actual, str):
                errors.append(f"{path} must be string or null")
            return
        if actual != expected:
            errors.append(f"{path} must equal {expected!r}")

    visit(template, payload, "")
    return errors
