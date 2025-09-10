import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Literal


class FormAccessCreate(BaseModel):
    form_id: Optional[uuid.UUID] = None
    user_ids: Optional[List[uuid.UUID]] = None
    access_type: Literal["individual", "all"]


class FormAccessResponse(BaseModel):
    access_id: uuid.UUID
    form_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    access_type: str
    created_by: uuid.UUID
    created_at: datetime


class NotificationResponse(BaseModel):
    type: str
    message: str
    user_id: Optional[uuid.UUID] = None
    user_name: Optional[str] = None


class FormAccessResult(BaseModel):
    success: List[FormAccessResponse]
    skipped: List[str]
    notifications_created: List[NotificationResponse]


class AssignedUser(BaseModel):
    user_id: uuid.UUID
    username: str


class FormWithAccessResponse(BaseModel):
    form_id: uuid.UUID
    title: str
    description: str
    created_by: uuid.UUID
    created_at: datetime
    is_active: bool
    assigned_users: List[AssignedUser]
