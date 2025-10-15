import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class NotificationCountResponse(BaseModel):
    user_id: uuid.UUID
    unread_count: int


class MarkReadRequest(BaseModel):
    notification_id: int


class MarkReadResponse(BaseModel):
    notification_id: str
    status: str
    message: str


class NotificationResponse(BaseModel):
    notification_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    form_id: Optional[str]
    form_title: Optional[str]
    access_type: str


class PaginationResponse(BaseModel):
    total_count: int
    total_pages: int
    current_page: int
    limit: int
    next_page: bool
    previous_page: bool


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    pagination: PaginationResponse