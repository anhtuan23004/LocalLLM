import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VariantSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("variant name must not be empty")
        return normalized


class FieldSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_key: str
    data_type: Literal["string", "number", "boolean", "date", "array"]
    field_name: str | None = None
    description: str | None = None
    nullable: bool = True
    required: bool = True
    child_schema: list["FieldSchema"] | None = None

    @field_validator("field_key")
    @classmethod
    def validate_field_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field_key must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_array_shape(self):
        if self.data_type == "array" and not self.child_schema:
            raise ValueError("child_schema is required when data_type is 'array'")
        if self.data_type != "array" and self.child_schema is not None:
            raise ValueError("child_schema is only allowed when data_type is 'array'")
        return self


class DocumentGroupSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_code: str
    group_name: str
    group_description: str
    variants: list[VariantSchema] = Field(default_factory=list)

    @field_validator("group_code")
    @classmethod
    def validate_group_code(cls, value: str) -> str:
        normalized = value.strip()
        if not re.fullmatch(r"[a-z0-9_]+", normalized):
            raise ValueError("group_code must match pattern ^[a-z0-9_]+$")
        return normalized

    @field_validator("group_name", "group_description")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("group_name and group_description must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_unique_variants(self):
        names = [variant.name.casefold() for variant in self.variants]
        if len(names) != len(set(names)):
            raise ValueError("variant name values must be unique per group")
        return self


class ExtractionGroupSchema(DocumentGroupSchema):
    fields: list[FieldSchema] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_fields(self):
        if self.group_code != "unknown" and not self.fields:
            raise ValueError("fields must contain at least one field for non-unknown groups")
        keys = [field.field_key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("field_key values must be unique per group")
        return self

    def as_group_schema(self) -> DocumentGroupSchema:
        return DocumentGroupSchema(
            group_code=self.group_code,
            group_name=self.group_name,
            group_description=self.group_description,
            variants=self.variants,
        )


class RequestBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_url: str

    @field_validator("file_url")
    @classmethod
    def validate_file_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("file_url must be a valid HTTP/HTTPS URL")
        return normalized


class ClassifySegmentRequest(RequestBase):
    extraction_schemas: list[DocumentGroupSchema]

    @field_validator("extraction_schemas")
    @classmethod
    def validate_schemas_not_empty(
        cls, value: list[DocumentGroupSchema]
    ) -> list[DocumentGroupSchema]:
        if not value:
            raise ValueError("extraction_schemas must contain at least one group")
        return value

    @model_validator(mode="after")
    def validate_unique_group_codes(self):
        codes = [schema.group_code for schema in self.extraction_schemas]
        if len(codes) != len(set(codes)):
            raise ValueError("group_code values must be unique")
        return self


class ExtractRequest(RequestBase):
    extraction_schemas: list[ExtractionGroupSchema]

    @field_validator("extraction_schemas")
    @classmethod
    def validate_schemas_not_empty(
        cls, value: list[ExtractionGroupSchema]
    ) -> list[ExtractionGroupSchema]:
        if not value:
            raise ValueError("extraction_schemas must contain at least one group")
        return value

    @model_validator(mode="after")
    def validate_unique_group_codes(self):
        codes = [schema.group_code for schema in self.extraction_schemas]
        if len(codes) != len(set(codes)):
            raise ValueError("group_code values must be unique")
        return self

    def classify_request(self) -> ClassifySegmentRequest:
        return ClassifySegmentRequest(
            file_url=self.file_url,
            extraction_schemas=[schema.as_group_schema() for schema in self.extraction_schemas],
        )


class DuplicatePage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    duplicate_of: int


class ClassifySegmentDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_code: str
    group_name: str
    document_name: str
    page_ranges: list[tuple[int, int]]
    page_order: list[int]
    duplicate_pages: list[DuplicatePage] = Field(default_factory=list)


class ClassifySegmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[ClassifySegmentDocument]


class ExtractedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_code: str
    group_name: str
    document_name: str
    page_order: list[int]
    duplicate_pages: list[DuplicatePage] = Field(default_factory=list)
    extracted_data: dict[str, Any]


class ExtractResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[ExtractedDocument]
