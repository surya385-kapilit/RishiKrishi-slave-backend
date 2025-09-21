import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.Models.form_submittions import ExportRequest, FlagRequest, FormBySubmissionResponse, FormSubmissionRequest, FormSubmissionResponse, FormUpdateRequest, FormUpdateResponse, PresignedUrlRequest, PresignedUrlResponse
from app.configuration.s3service import S3Service
from app.service.FormService import FormService
from app.service.form_submittions_service import FormSubmissions

logger = logging.getLogger(__name__)

form_submissions_router = APIRouter(prefix="/api/forms/submissions", tags=["Tasks"])

flag_submission_router = APIRouter(prefix="/api", tags=["Flaged Submissions"])
filter_router = APIRouter(prefix="/api", tags=["Reports"])

# data can be submitted by either admin or user
@form_submissions_router.post("/submit-form", response_model=FormSubmissionResponse)
async def submit_form(
    request: Request,
    form_data: str = Form(...),  # JSON as string in multipart requests
    files: Optional[List[UploadFile]] = File(None),  # Expected files field
):
    form = await request.form()
    logger.debug(f"Received form fields: {form.keys()}")
    logger.debug(f"Received files: {files}")

    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    submitted_by = user_payload.get("sub")  # token "sub" claim as user ID

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    try:
        form_data_dict = json.loads(form_data)

        # Convert any array values properly
        if "field_values" in form_data_dict:
            for field_value in form_data_dict["field_values"]:
                if isinstance(field_value.get("value"), str):
                    if field_value["value"].startswith("[") and field_value["value"].endswith("]"):
                        try:
                            field_value["value"] = json.loads(field_value["value"])
                        except json.JSONDecodeError:
                            pass
        parsed_data = FormSubmissionRequest(**form_data_dict)
    except Exception as e:
        logger.error(f"Invalid form_data JSON: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid form_data JSON: {str(e)}")

    service = FormSubmissions(schema_id)
    s3 = S3Service()

    try:
        return await service.submit_form_with_files(
            form_id=str(parsed_data.form_id),
            submitted_by=submitted_by,
            field_values=parsed_data.field_values,
            files=files,
            s3=s3,
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in submit_form: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Update form fields after submission
@form_submissions_router.put("/update/{submission_id}", response_model=FormUpdateResponse)
async def update_form(
    submission_id: str,
    request: Request,
    form_data: str = Form(...),  # JSON as string in multipart requests
    files: Optional[List[UploadFile]] = File(None),
):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    submitted_by = user_payload.get("sub")
    

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")
    
    try:
        form_data_dict = json.loads(form_data)
        parsed_data = FormUpdateRequest(**form_data_dict)  # ✅ use update model
        
    except Exception as e:
        # logger.error(f"Invalid form_data JSON: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid form_data JSON")

    service = FormSubmissions(schema_id)
    s3 = S3Service()
    try:
        return await service.update_form_with_files(
            submission_id=submission_id,
            form_id=str(parsed_data.form_id),
            submitted_by=submitted_by,
            field_values=parsed_data.field_values or [],  # ✅ safe default
            files=files,
            s3=s3,
            parsed_data=parsed_data,
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        # logger.error(f"Error in update_form: {str(e)}") 
        raise HTTPException(status_code=400, detail=str(e))


@form_submissions_router.get("/get-form-data/{submission_id}", response_model=FormBySubmissionResponse)
async def get_form_submission(submission_id: str, request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("sub")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    service = FormSubmissions(schema_id)
    try:
        submission = service.get_form_by_submission_id(submission_id, user_id)
        return submission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching submission {submission_id}: {str(e)}")
        raise HTTPException(status_code=400, detail="Something went wrong")




# get all submissions with filters and pagination

@filter_router.get("/filter/submissions")
async def get_all_submissions(
    request: Request,
    form_id: Optional[str] = None,
    task_id: Optional[str] = None,
    submitted_by: Optional[str] = None,   # will be ignored for non-admins
    flagged: Optional[str] = None,
    start_date: Optional[str] = None,     # dd-mm-yyyy
    end_date: Optional[str] = None,       # dd-mm-yyyy
    page: int = 0,
    limit: int = 10
):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    role = user_payload.get("role")
    user_id_token = user_payload.get("sub")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    # Non-admins: force filter by their own user_id
    if role.lower() != "admin":
        if submitted_by and submitted_by != user_id_token:
            raise HTTPException(status_code=403, detail="User not authorized to access this resource")
        # force user_id to token value
        submitted_by = user_id_token

    service = FormSubmissions(schema_id)

    try:
        submissions, total_count = await service.get_all_submissions(
            form_id=form_id,
            task_id=task_id,
            submitted_by=submitted_by,
            flagged=flagged,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
            is_admin=(role.lower() == "admin")  # pass admin flag
        )
        return {
            "page": page,
            "limit": limit,
            "total_submissions": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "submissions": submissions
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching submissions: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))



# get submissions by the logged-in user
@form_submissions_router.get("/get-my-data")
async def get_my_form_submissions(
    request: Request,
    form_id: Optional[str] = None,  # optional filter
    page: int = 0,
    limit: int = 10):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("sub")
    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing schema_id or user_id in token")

    service = FormSubmissions(schema_id)
    try:
        submissions, total_count = await service.get_my_form_submissions(
            form_id=form_id, user_id=user_id, page=page, limit=limit
        )

        return {
            "user_id": user_id,
            "total_submissions": total_count,
            "page": page,
            "limit": limit,
            "forms": submissions   # grouped by forms
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching user's form submissions: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
# get submissions by a specific user
@form_submissions_router.get("/my-submissions/{user_id}")
async def get_submissions_by_user(
    request: Request,
    user_id: str,
    form_id: Optional[str] = None,  # optional filter
    page: int = 0,
    limit: int = 10,
):


    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    role = user_payload.get("role")
    user_id_token = user_payload.get("sub")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    # Role-based access
    if role.lower() != "admin" and user_id != user_id_token:
        raise HTTPException(status_code=403, detail="User not authorized to view these submissions")

    service = FormSubmissions(schema_id)

    try:
        # Get submissions
        submissions = await service.get_submissions_by_user(
            user_id=user_id, form_id=form_id, page=page, limit=limit
        )

        # Count total submissions (for pagination info)
        total_count = await service.count_submissions_by_user(user_id=user_id, form_id=form_id)
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

        return {
            "user_id": user_id,
            "total_submissions": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "submissions": submissions,
        }

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"Error fetching submissions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    
# raised, approved, rejected
@form_submissions_router.put("/flag/{submission_id}")
async def flag_submission(
    submission_id: str,
    request: Request,
    body: FlagRequest  # 'raised', 'approved', 'rejected'
):
    flag_status = body.flag_status.lower()
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("sub")
    role = user_payload.get("role")
    if submission_id is None or submission_id.strip() == "":
        raise HTTPException(status_code=400, detail="submission_id is required")

    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing schema_id or user_id in token")

    if flag_status not in ["raised", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid flag_status value")

    service = FormSubmissions(schema_id)

    try:
        result = await service.flag_submission(
            submission_id=submission_id,
            flagged_by=user_id,
            flag_status=flag_status,
            is_admin=(role.lower() == "admin"),
        )
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error flagging submission {submission_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    


@form_submissions_router.post(
    "/presigned-url/upload", response_model=PresignedUrlResponse)
async def generate_upload_presigned_urls(
    request_body: PresignedUrlRequest, request: Request
):
    user_payload = request.state.user  # assuming you attach user in middleware
    role = user_payload.get("role")  # <-- check role here
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ✅ New role check
    if not role or role.lower() not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Unauthorized user")

    try:
        s3 = S3Service()
        presigned_urls = {}

        # Handle folder logic
        folder_path = ""
        if request_body.folder and request_body.folder.strip():
            folder_path = request_body.folder.strip()
            if not folder_path.endswith("/"):
                folder_path += "/"

        # Loop through all files
        for file_name in request_body.fileNames:
            object_name = folder_path + file_name
            url = s3.generate_upload_presigned_url(
                object_name, request_body.expiryHours
            )
            presigned_urls[file_name] = url

        return PresignedUrlResponse(
            success=True,
            presignedUrls=presigned_urls,
            folder=request_body.folder,
            count=len(presigned_urls),
            expiryHours=request_body.expiryHours,
            method="PUT",
            message="Upload presigned URLs generated successfully",
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating presigned URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@form_submissions_router.post("/export")
async def export_submissions(
    request: Request,
    export_request: ExportRequest
):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    role = user_payload.get("role")
    user_id_token = user_payload.get("sub")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Missing schema_id in token")

    # Non-admins: restrict to their own submissions
    if role.lower() != "admin":
        if export_request.submitted_by and export_request.submitted_by != user_id_token:
            raise HTTPException(status_code=403, detail="User not authorized to access this resource")
        export_request.submitted_by = user_id_token

    service = FormSubmissions(schema_id)

    try:
        # Fetch submissions with detailed field values + pagination metadata
        submissions_response = await service.export_submissions(
            form_id=export_request.form_id,
            task_id=export_request.task_id,
            submitted_by=export_request.submitted_by,
            flagged=export_request.flagged,
            start_date=export_request.start_date,
            end_date=export_request.end_date,
            page=export_request.page,
            limit=export_request.limit,
            is_admin=(role.lower() == "admin")
        )

        submissions = submissions_response["submissions"]

        # Transform into consistent task/form/submission structure
        tasks_result = []
        task_map = {}

        for submission in submissions:
            task_id = submission["task_id"]
            task_name = submission["task_name"]
            form_id = submission["form_id"]
            form_title = submission["form_title"]

            # Ensure task exists
            if task_id not in task_map:
                task_obj = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "forms": []
                }
                task_map[task_id] = task_obj
                tasks_result.append(task_obj)

            task_obj = task_map[task_id]

            # Ensure form exists under this task
            form_obj = next((f for f in task_obj["forms"] if f["form_id"] == form_id), None)
            if not form_obj:
                form_obj = {
                    "form_id": form_id,
                    "form_title": form_title,
                    "submissions": []
                }
                task_obj["forms"].append(form_obj)

            # Add submission
            form_obj["submissions"].append({
                "submission_id": submission["submission_id"],
                "submitted_by": submission["submitted_by"],
                "submitted_at": submission["submitted_at"],
                "flagged": submission["flagged"],
                "field_values": [
                    {"field_name": f["field_name"], "value": f["value"]}
                    for f in submission["field_values"]
                ]
            })

        # Merge pagination metadata + tasks
        return {
            "page": submissions_response["page"],
            "limit": submissions_response["limit"],
            "total_submissions": submissions_response["total_submissions"],
            "total_pages": submissions_response["total_pages"],
            "tasks": tasks_result
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error exporting submissions: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
