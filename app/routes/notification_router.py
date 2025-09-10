from fastapi import APIRouter, Depends, Query, Request, HTTPException
from typing import List, Optional

from app.Models.notification import (
    MarkReadRequest,
    MarkReadResponse,
    NotificationCountResponse,
)
from app.service.NotificationService import NotificationService


notification_router = APIRouter()
notification_router = APIRouter(prefix="/api/notify", tags=["notify"])


@notification_router.get("/count", response_model=NotificationCountResponse)
def get_unread_count(request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("sub")  # take from token (sub = user_id in your payload)

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    service = NotificationService(schema_id)
    try:
        return service.get_unread_count(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@notification_router.post("/mark_read", response_model=MarkReadResponse)
def mark_as_read(request_data: MarkReadRequest, request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("sub")  # ✅ user comes from JWT, not path param

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    service = NotificationService(schema_id)
    try:
        return service.mark_as_read(str(request_data.notification_id), str(user_id))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@notification_router.get("/list")
@notification_router.get("/list/{status}")  # optional filter: read/unread 5c1ee55c-949f-4803-a666-918d34a82d2c  31
def list_notifications(
    request: Request,
    status: Optional[str] = None,   # can be "read", "unread", or None
    page: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("sub")
    role = user_payload.get("role")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if status not in (None, "read", "unread"):
        raise HTTPException(status_code=400, detail="Invalid status filter")

    service = NotificationService(schema_id)
    return service.list_notifications(str(user_id), role, page, limit, status)
