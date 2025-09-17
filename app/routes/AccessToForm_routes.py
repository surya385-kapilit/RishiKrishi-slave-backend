from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request

from app.Models.AccessToForm import FormAccessCreate, FormAccessResponse
from app.service.AccessToForm_service import FormAccessService


AccessToForm_routes = APIRouter(prefix="/api/form-access", tags=["Form Access"])


@AccessToForm_routes.post("/add")
def create_form_access(access_data: FormAccessCreate, request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    role = user_payload.get("role")
    schema_id = user_payload.get("schema_id")
    created_by = user_payload.get("sub")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormAccessService(schema_id)
    try:
        return service.create_access(access_data, created_by)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@AccessToForm_routes.delete("/delete")
def delete_form_access(form_id: str, request: Request, user_id: Optional[str] = None):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    role = user_payload.get("role")
    schema_id = user_payload.get("schema_id")
    deleted_by = user_payload.get("sub")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormAccessService(schema_id)
    try:
        return service.delete_access(form_id, user_id, deleted_by)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@AccessToForm_routes.get("/list")
def get_forms(request: Request, form_id: str = None):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    service = FormAccessService(schema_id)
    try:
        return service.get_form_with_access(form_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@AccessToForm_routes.get("/my-forms")
def get_my_forms(
    request: Request,
    page: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    user_payload = request.state.user

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    role = user_payload.get("role")
    user_id = user_payload.get("sub")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "supervisor":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormAccessService(schema_id)
    try:
        forms, total_count = service.get_forms_for_user(user_id, page, limit)
        if not forms:
            return {"message": "There are no forms available for you"}
        
        total_pages = (total_count + limit - 1) // limit
        return {
            "assigned_forms": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "forms": forms,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

