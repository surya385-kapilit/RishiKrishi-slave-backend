from click import UUID
from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    phone: Optional[str]
    status: str
    admin_name: str

class UsersListResponse(BaseModel):
    user_id: str
    name: str


