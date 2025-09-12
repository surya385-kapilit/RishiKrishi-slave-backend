from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.Models.AccessToForm import FormAccessCreate, FormAccessResult


class FieldOption(BaseModel):
    field_id: Optional[UUID] = None
    name: str
    field_type: str  # e.g., "radio", "text", "files", etc.
    is_required: bool
    field_options: Optional[List[str]] = None


class FormCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_id: Optional[UUID] = None
    fields: List[FieldOption]
    created_by: Optional[UUID] = None


class CreateFormRequest(BaseModel):
    form_data: FormCreate
    assign_data: Optional[FormAccessCreate] = None

class FormCreationResponse(BaseModel):
    message: str
    form: FormCreate


class FormResponse(BaseModel):
    form_id: UUID
    task_id: Optional[UUID]
    title: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    is_active: Optional[bool] = True
    # fields: List[FieldOption]
class GetAllFormsResponse(BaseModel):
    form_id: UUID
    task_id: Optional[UUID]
    title: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    is_active: bool


class FormsListResponse(BaseModel):
    form_id: UUID
    title: str
    is_active: bool


class CreateFormResponse(BaseModel):
    # messsage: str
    form: FormResponse
    
#Form Creation Response    
class FormCreationResponse(BaseModel):
    message: str
    form_id: UUID
    task_id: Optional[UUID]
    title: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    # form: FormResponse



class FormResponseWithFields(FormResponse):
    fields: List[FieldOption]


class FormFieldsResponse(BaseModel):
    form_id: UUID
    fields: List[FieldOption]


class PaginatedFormsResponse(BaseModel):
    page: int
    limit: int
    total_forms: int
    total_pages: int
    forms: List[GetAllFormsResponse]


class FormInDB(BaseModel):
    form_id: UUID
    task_id: Optional[UUID]
    title: str
    description: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime


class FieldInDB(BaseModel):
    field_id: UUID
    form_id: UUID
    name: str
    field_type: str
    is_required: bool
    field_options: Optional[List[str]] = None
