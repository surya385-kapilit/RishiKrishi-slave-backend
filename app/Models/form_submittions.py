from uuid import UUID
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class FieldValue(BaseModel):
    field_id: UUID
    value: Union[str, List[str], None] = Field(None)  # text or file URL


class FileMapping(BaseModel):
    field_id: UUID
    file_index: int  # Index of the file in the uploaded files list


class FormSubmissionRequest(BaseModel):
    form_id: UUID
    submitted_by: Optional[UUID] = None
    field_values: List[FieldValue]
    file_mappings: Optional[List[FileMapping]] = None  # New field for file mappings


class FormSubmissionResponse(BaseModel):
    submission_id: UUID
    message: str
    submitted_at: datetime
    
    

# ---------------- New for Update ----------------
class FormUpdateRequest(BaseModel):
    form_id: UUID
    field_values: Optional[List[FieldValue]] = None   # Optional for partial update
    file_mappings: Optional[List[FileMapping]] = None # Optional for updating files

class FormUpdateResponse(BaseModel):
    message: str
    # submission_id: UUID
    # updated_at: datetime


class FlagRequest(BaseModel):
    flag_status: str

class FieldValueResponse(BaseModel):
    field_id: UUID
    field_name: str
    value: Any 


class FormBySubmissionResponse(BaseModel):
    submission_id: UUID
    form_id: UUID
    form_title: str
    submitted_by: str
    submitted_at: datetime
    flagged: Optional[str]
    field_values: List[FieldValueResponse]