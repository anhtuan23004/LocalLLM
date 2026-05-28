from .schemas import ClassifySegmentDocument, DocumentGroupSchema, ExtractionGroupSchema, FieldSchema


def classify_prompt(groups: list[DocumentGroupSchema], page_count: int) -> str:
    group_lines: list[str] = []
    for group in groups:
        variants = ", ".join(
            f"{variant.name} ({variant.description})" if variant.description else variant.name
            for variant in group.variants
        ) or "None"
        group_lines.append(
            "\n".join(
                [
                    f'- group_code/document_code: "{group.group_code}"',
                    f"  group_name: {group.group_name}",
                    f"  group_description: {group.group_description}",
                    f"  variants/sample titles: {variants}",
                ]
            )
        )

    unknown_rule = (
        'Use document_code "unknown" only if the provided schema list includes group_code "unknown". '
        "Otherwise ignore documents that do not match a provided group."
    )

    return (
        "You are an expert document classification and segmentation system.\n"
        f"The input contains {page_count} page image(s), provided in physical page order.\n\n"
        "Allowed document groups:\n"
        f"{chr(10).join(group_lines)}\n\n"
        "Return every logical document matching one of the allowed groups.\n"
        "document_code must be the matched group_code. group_name must be the canonical group_name.\n"
        "document_name must be the real title observed on the document; if unreadable, use the closest variant or group_name.\n"
        f"{unknown_rule}\n\n"
        "For each document return page_ranges, page_order, and duplicate_pages.\n"
        "page_order is a flat array of physical page numbers in logical reading order.\n"
        "page_ranges is an array of [start_page, end_page] physical page ranges. Use separate ranges for non-adjacent pages.\n"
        "duplicate_pages lists duplicate scans as {page, duplicate_of}; duplicate pages must not appear in page_order or page_ranges.\n"
        "Return only JSON matching the requested schema."
    )


def extraction_prompt(group: ExtractionGroupSchema, document: ClassifySegmentDocument) -> str:
    if group.group_code == "unknown" and not group.fields:
        schema_description = (
            "Unknown document. Extract readable non-table key-value fields into fields[] and tabular content into tables[]. "
            "Use English snake_case keys and keep field/table labels in the original document language. "
            "For table rows, output cells as an array of {key, value} objects."
        )
    else:
        field_lines = [field_description(field) for field in group.fields]
        schema_description = "\n".join(field_lines)

    return (
        "You are an expert document extraction system.\n"
        f'Document code: "{document.document_code}".\n'
        f"Canonical group name: {document.group_name}.\n"
        f"Observed document name: {document.document_name}.\n"
        f"Physical pages supplied for this document: {document.page_order}.\n\n"
        "Extract only the requested structured data for this document.\n"
        "If a requested field or value is not visible, set that field to null.\n"
        "Do not infer values from neighboring labels or unrelated rows.\n"
        "For date fields, use ISO 8601 format YYYY-MM-DD when the date is clear.\n"
        "For number fields, output a JSON number without currency symbols or thousand separators.\n"
        "For boolean fields, output true only when a real mark/tick/affirmative value is present; otherwise false.\n\n"
        "Fields/schema:\n"
        f"{schema_description}\n\n"
        "Return only JSON matching the requested schema."
    )


def field_description(field: FieldSchema) -> str:
    hint = field.description or field.field_name or ""
    if field.data_type == "array":
        children = ", ".join(field_description(child) for child in (field.child_schema or []))
        descriptor = f"- {field.field_key} (array of objects: {children})"
    else:
        descriptor = f"- {field.field_key} ({field.data_type})"
    if hint:
        descriptor += f" - Hint: {hint}"
    return descriptor
