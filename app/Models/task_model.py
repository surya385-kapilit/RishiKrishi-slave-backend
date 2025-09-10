
import uuid
from pydantic import BaseModel, Field
from typing import Optional,List
from uuid import UUID
from datetime import datetime


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    created_by: Optional[UUID] = None  # Will be set from JWT token in route


class TaskResponse(BaseModel):
    task_id: UUID
    name: str
    description: Optional[str]
    created_by: Optional[str] = None
    created_at: Optional[datetime]
    # form_count: int = 0 
    form_count: Optional[int] = 0

class TaskListResponse(BaseModel):
    task_id: UUID
    title: str

    
class TaskCreationResponse(BaseModel):
    task_id: UUID
    name: str
    description: Optional[str]
    created_by: str 
    created_at: datetime
    # form_count: int = 0
    
class PaginatedTasksResponse(BaseModel):
    page: int
    limit: int
    total_tasks: int
    total_pages: int
    tasks: List[TaskResponse]


class TaskUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    created_by: Optional[UUID] = None


class TaskIdsRequest(BaseModel):
    task_ids: List[uuid.UUID]