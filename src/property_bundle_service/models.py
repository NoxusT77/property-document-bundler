from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class DocumentKind(StrEnum):
    MAINTENANCE_REQUEST = "maintenance_request"
    TENANT_DOCUMENT = "tenant_document"
    INSPECTION_REMINDER = "inspection_reminder"


class PropertyDocument(BaseModel):
    document_id: str = Field(min_length=1)
    kind: DocumentKind
    pdf_base64: str = Field(min_length=1)
    urgent: bool = False

    @model_validator(mode="after")
    def urgent_only_applies_to_maintenance(self) -> "PropertyDocument":
        if self.urgent and self.kind is not DocumentKind.MAINTENANCE_REQUEST:
            raise ValueError("only maintenance requests can be urgent")
        return self


class MergeBundleRequest(BaseModel):
    property_id: str = Field(min_length=1)
    documents: list[PropertyDocument] = Field(min_length=1)


class MergeBundleResult(BaseModel):
    property_id: str
    ordered_document_ids: list[str]
    merge: dict[str, object]


class PageRange(BaseModel):
    name: str = Field(min_length=1)
    start: int = Field(ge=1)
    end: int = Field(ge=1)

    @model_validator(mode="after")
    def range_is_forward(self) -> "PageRange":
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        return self
