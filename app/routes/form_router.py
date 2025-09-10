from typing import List, Optional
import uuid
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse as JsonResponse

from app.Models.AccessToForm import FormAccessCreate
from app.Models.form_model import (
    CreateFormRequest,
    CreateFormResponse,
    FormCreate,
    FormCreationResponse,
    FormFieldsResponse,
    FormResponse,
    FormResponseWithFields,
    FormsListResponse,
    PaginatedFormsResponse,
)
from app.service.AccessToForm_service import FormAccessService
from app.service.FormService import FormService

form_router = APIRouter(prefix="/api/forms", tags=["Tasks"])

# Create a new form
@form_router.post("/create", response_model=FormCreationResponse)
def create_form(request_data: CreateFormRequest, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("user_id") or user_payload.get("sub")

    if not schema_id or not user_id:
        raise HTTPException(
            status_code=400, detail="Missing schema_id or user_id in token"
        )

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    form_data = request_data.form_data
    assign_data = request_data.assign_data

    form_data.created_by = uuid.UUID(user_id)

    service = FormService(schema_id)
    access_service = FormAccessService(schema_id)

    try:
        # Step 1: Create form
        created_form = service.create_form(form_data)

        # Step 2: Assign access if assign_data provided
        access_result = None
        if assign_data:
            assign_data.form_id = created_form.form_id
            print("form_created:",)
            access_result = access_service.create_access(
                access_data=assign_data, created_by=user_id
            )

        return {
            "message": "Form created successfully",
            "form_id": created_form.form_id,
            "task_id": created_form.task_id,
            "title": created_form.title,
            "description": created_form.description,
            "created_by": str(created_form.created_by),
            "created_at": created_form.created_at
            # "access": access_result or {"message": "No access assigned"},
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Update form 
@form_router.put("/{form_id}", response_model=FormResponse)
def edit_form(form_id: str, form_data: FormCreate, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("user_id") or user_payload.get("sub")

    if not schema_id or not user_id:
        raise HTTPException(
            status_code=400, detail="Missing schema_id or user_id in token"
        )

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    form_data.created_by = uuid.UUID(user_id)

    service = FormService(schema_id)
    try:
        return service.update_form(form_id, form_data)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET single form with fields
@form_router.get("/{form_id}", response_model=FormResponseWithFields)
def get_form(form_id: str, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormService(schema_id)
    try:
        return service.get_form(form_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@form_router.get("/{form_id}/fields", response_model=FormFieldsResponse)
def get_form(form_id: str, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormService(schema_id)
    try:
        return service.get_form_fields(form_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


#Get forms-list by task id
@form_router.get("/a/{task_id}/forms-list", response_model=List[FormsListResponse])
def get_forms_list_by_task(task_id: str, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormService(schema_id)
    try:
        return service.get_forms_list_by_task(task_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Get forms by task with pagination
@form_router.get("/tasks/{task_id}/forms", response_model=PaginatedFormsResponse)
def get_forms_by_task(task_id: str, request: Request, page: int = 1, limit: int = 10):
    user_payload = request.state.user
    role = user_payload.get("role")

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormService(schema_id)
    try:
        return service.get_forms_by_task(task_id, page=page, limit=limit)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# DELETE form
@form_router.delete("/{form_id}")
def delete_form(form_id: str, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormService(schema_id)
    try:
        service.delete_form(form_id)
        return {"message": "Form deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE specific field from a form
@form_router.delete("/{form_id}/fields/{field_id}")
def delete_form_field(form_id: str, field_id: str, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormService(schema_id)
    try:
        service.delete_form_field(form_id, field_id)
        return {"message": "Field deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# update status of the form like is_active status
@form_router.put("/{form_id}/change_status")
def update_form_status(form_id: str, request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    role = user_payload.get("role")
    schema_id = user_payload.get("schema_id")
    admin_name = user_payload.get("username")  # take admin name from token

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = FormService(schema_id)
    try:
        result = service.update_form_status(form_id,updated_by=admin_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
