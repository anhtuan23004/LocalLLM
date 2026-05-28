from typing import Any

from fastapi import HTTPException

from .documents import LoadedDocument, load_document
from .model_client import VisionModelClient
from .prompts import classify_prompt, extraction_prompt
from .schemas import (
    ClassifySegmentDocument,
    ClassifySegmentRequest,
    ClassifySegmentResponse,
    ExtractRequest,
    ExtractResponse,
    ExtractedDocument,
    ExtractionGroupSchema,
    FieldSchema,
)
from .structured import classify_response_schema, extraction_response_schema, strict_response_format


class OcrPipeline:
    def __init__(self, model_client: VisionModelClient | None = None):
        self.model_client = model_client or VisionModelClient()

    async def classify_segment(self, request: ClassifySegmentRequest) -> ClassifySegmentResponse:
        document = await load_document(request.file_url)
        return await self.classify_loaded_document(request, document)

    async def classify_loaded_document(
        self, request: ClassifySegmentRequest, document: LoadedDocument
    ) -> ClassifySegmentResponse:
        payload = await self.model_client.complete_json(
            prompt=classify_prompt(request.extraction_schemas, len(document.pages)),
            pages=document.pages,
            response_format=strict_response_format(
                "ocr_v1_classify_segment",
                classify_response_schema(request.extraction_schemas),
            ),
        )
        try:
            response = ClassifySegmentResponse.model_validate(payload)
            return normalize_classification_response(
                response,
                allowed_groups={schema.group_code: schema.group_name for schema in request.extraction_schemas},
                page_count=len(document.pages),
            )
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=f"model response failed validation: {exc}") from exc

    async def extract(self, request: ExtractRequest) -> ExtractResponse:
        document = await load_document(request.file_url)
        classification = await self.classify_loaded_document(request.classify_request(), document)
        schema_map = {schema.group_code: schema for schema in request.extraction_schemas}
        extracted_documents: list[ExtractedDocument] = []

        for classified_doc in classification.documents:
            group_schema = schema_map[classified_doc.document_code]
            page_images = document.pages_by_number(classified_doc.page_order)
            extracted_data = await self.extract_document(group_schema, classified_doc, page_images)
            extracted_documents.append(
                ExtractedDocument(
                    document_code=classified_doc.document_code,
                    group_name=classified_doc.group_name,
                    document_name=classified_doc.document_name,
                    page_order=classified_doc.page_order,
                    duplicate_pages=classified_doc.duplicate_pages,
                    extracted_data=extracted_data,
                )
            )

        return ExtractResponse(documents=extracted_documents)

    async def extract_document(
        self,
        group_schema: ExtractionGroupSchema,
        classified_doc: ClassifySegmentDocument,
        page_images,
    ) -> dict[str, Any]:
        payload = await self.model_client.complete_json(
            prompt=extraction_prompt(group_schema, classified_doc),
            pages=page_images,
            response_format=strict_response_format(
                f"ocr_v1_extract_{group_schema.group_code}",
                extraction_response_schema(group_schema),
            ),
        )
        try:
            return normalize_extracted_data(group_schema, payload)
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=f"model extraction failed validation: {exc}") from exc


def normalize_classification_response(
    response: ClassifySegmentResponse,
    *,
    allowed_groups: dict[str, str],
    page_count: int,
) -> ClassifySegmentResponse:
    normalized_docs: list[ClassifySegmentDocument] = []
    used_pages: set[int] = set()

    for doc in response.documents:
        if doc.document_code not in allowed_groups:
            continue
        if not doc.document_name:
            doc.document_name = allowed_groups[doc.document_code]
        doc.group_name = allowed_groups[doc.document_code]
        validate_page_metadata(doc, page_count)

        range_pages = pages_from_ranges(doc.page_ranges)
        overlap = used_pages.intersection(range_pages)
        if overlap:
            raise ValueError(f"page_ranges overlap across documents: {sorted(overlap)}")
        used_pages.update(range_pages)
        normalized_docs.append(doc)

    return ClassifySegmentResponse(documents=normalized_docs)


def validate_page_metadata(doc: ClassifySegmentDocument, page_count: int) -> None:
    if not doc.page_order:
        raise ValueError("page_order must not be empty")
    if not doc.page_ranges:
        raise ValueError("page_ranges must not be empty")

    all_pages = set(range(1, page_count + 1))
    page_order_set = set(doc.page_order)
    range_pages = pages_from_ranges(doc.page_ranges)
    if len(page_order_set) != len(doc.page_order):
        raise ValueError("page_order must not contain duplicate pages")
    if not page_order_set.issubset(all_pages):
        raise ValueError("page_order references a page outside the file")
    if not range_pages.issubset(all_pages):
        raise ValueError("page_ranges reference a page outside the file")
    if page_order_set != range_pages:
        raise ValueError("page_order must match the union of page_ranges")

    duplicate_pages = {duplicate.page for duplicate in doc.duplicate_pages}
    duplicate_targets = {duplicate.duplicate_of for duplicate in doc.duplicate_pages}
    if duplicate_pages.intersection(page_order_set):
        raise ValueError("duplicate_pages must not appear in page_order")
    if not duplicate_pages.issubset(all_pages):
        raise ValueError("duplicate_pages reference a page outside the file")
    if not duplicate_targets.issubset(page_order_set):
        raise ValueError("duplicate_of must reference a page in page_order")


def pages_from_ranges(page_ranges: list[tuple[int, int]]) -> set[int]:
    pages: set[int] = set()
    for start_page, end_page in page_ranges:
        if start_page < 1 or end_page < 1 or end_page < start_page:
            raise ValueError("page_ranges must contain positive [start_page, end_page] pairs")
        current = set(range(start_page, end_page + 1))
        if pages.intersection(current):
            raise ValueError("page_ranges must be disjoint")
        pages.update(current)
    return pages


def normalize_extracted_data(group: ExtractionGroupSchema, payload: dict[str, Any]) -> dict[str, Any]:
    if group.group_code == "unknown" and not group.fields:
        validate_unknown_payload(payload)
        return payload

    expected_keys = {field.field_key for field in group.fields}
    extra_keys = set(payload) - expected_keys
    if extra_keys:
        raise ValueError(f"extracted_data contains unexpected keys: {sorted(extra_keys)}")

    return {
        field.field_key: normalize_field_value(field, payload.get(field.field_key))
        for field in group.fields
    }


def normalize_field_value(field: FieldSchema, value: Any) -> Any:
    if value is None:
        return None
    if field.data_type in {"string", "date"}:
        if not isinstance(value, str):
            raise ValueError(f"{field.field_key} must be a string or null")
        return value
    if field.data_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{field.field_key} must be a number or null")
        return value
    if field.data_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(f"{field.field_key} must be a boolean or null")
        return value
    if field.data_type == "array":
        if not isinstance(value, list):
            raise ValueError(f"{field.field_key} must be an array or null")
        return [normalize_array_item(field, item) for item in value]
    return value


def normalize_array_item(field: FieldSchema, item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"{field.field_key} array items must be objects")
    child_fields = field.child_schema or []
    expected_keys = {child.field_key for child in child_fields}
    extra_keys = set(item) - expected_keys
    if extra_keys:
        raise ValueError(f"{field.field_key} array item contains unexpected keys: {sorted(extra_keys)}")
    return {
        child.field_key: normalize_field_value(child, item.get(child.field_key))
        for child in child_fields
    }


def validate_unknown_payload(payload: dict[str, Any]) -> None:
    if set(payload) != {"fields", "tables"}:
        raise ValueError("unknown extracted_data must contain fields and tables")
    if not isinstance(payload["fields"], list) or not isinstance(payload["tables"], list):
        raise ValueError("unknown fields and tables must be arrays")
    for field in payload["fields"]:
        if not isinstance(field, dict) or set(field) != {"field_key", "field_name", "value"}:
            raise ValueError("unknown fields must contain field_key, field_name, and value")
    for table in payload["tables"]:
        if not isinstance(table, dict) or set(table) != {"table_key", "table_name", "columns", "rows"}:
            raise ValueError("unknown tables must contain table_key, table_name, columns, and rows")
        if not isinstance(table["columns"], list) or not isinstance(table["rows"], list):
            raise ValueError("unknown table columns and rows must be arrays")
        for column in table["columns"]:
            if not isinstance(column, dict) or set(column) != {"key", "label"}:
                raise ValueError("unknown table columns must contain key and label")
        for row in table["rows"]:
            if not isinstance(row, dict) or set(row) != {"cells"} or not isinstance(row["cells"], list):
                raise ValueError("unknown table rows must contain cells")
            for cell in row["cells"]:
                if not isinstance(cell, dict) or set(cell) != {"key", "value"}:
                    raise ValueError("unknown table row cells must contain key and value")
