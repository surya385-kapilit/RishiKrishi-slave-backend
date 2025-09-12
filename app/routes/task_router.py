import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.Models.task_model import (
    PaginatedTasksResponse,
    TaskCreate,
    TaskCreationResponse,
    TaskIdsRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.service.task_service import TaskService


task_router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@task_router.post("/create", response_model=TaskCreationResponse)
def create_task(task_data: TaskCreate, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")  # <-- check role here
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")

    user_id = user_payload.get("user_id") or user_payload.get("sub")

    if not schema_id or not user_id:
        raise HTTPException(
            status_code=400, detail="Missing schema_id or user_id in token"
        )

    # ✅ New role check
    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    # Inject user_id into task data
    task_data.created_by = user_id

    service = TaskService(schema_id)
    return service.create_task(task_data)

#get Favourite tasks by ids
@task_router.get("/favourite", response_model=List[TaskResponse])
def get_tasks(payload: TaskIdsRequest, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")
    schema_id = user_payload.get("schema_id")
    service = TaskService(schema_id)
    return service.get_tasks_by_ids(payload.task_ids)

#get tasks-list

@task_router.get("/list", response_model=List[TaskListResponse])
def get_tasks_list(request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("user_id") or user_payload.get("sub")
    role = user_payload.get("role")

    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id or schema_id")

    service = TaskService(schema_id)

    if role and role.lower() == "admin":
        tasks = service.get_tasks_list(uuid.UUID(user_id))
    else:
        tasks = service.get_tasks_list_for_user(uuid.UUID(user_id))

    return tasks



# @task_router.get("/list", response_model=List[TaskListResponse])
# def get_tasks_list(request: Request):
#     user_payload = request.state.user
#     role = user_payload.get("role")
#     if not user_payload:
#         raise HTTPException(status_code=401, detail="Unauthorized")

#     schema_id = user_payload.get("schema_id")
#     user_id = user_payload.get("user_id") or user_payload.get("sub")

#     if not schema_id or not user_id:
#         raise HTTPException(status_code=400, detail="Missing user_id or schema_id")

#     if not role or role.lower() != "admin":
#         raise HTTPException(status_code=403, detail="Unauthorized user")

#     service = TaskService(schema_id)
#     tasks = service.get_tasks_list(uuid.UUID(user_id))
#     return tasks

# get all tasks
@task_router.get("/all", response_model=PaginatedTasksResponse)
def get_all_tasks(request: Request, page: int = 1, limit: int = 10):
    user_payload = request.state.user
    role = user_payload.get("role")

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("user_id") or user_payload.get("sub")

    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id or schema_id")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = TaskService(schema_id)
    return service.get_all_tasks(uuid.UUID(user_id), page=page, limit=limit)


#get task by id
@task_router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: uuid.UUID, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("user_id") or user_payload.get("sub")

    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id or schema_id")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = TaskService(schema_id)
    task = service.get_task_by_id(task_id, uuid.UUID(user_id))

    if task:
        return task

    raise HTTPException(status_code=404, detail="Task not found or not owned by user")



# update task information
@task_router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: uuid.UUID,
    task_data: TaskUpdate,
    request: Request,
):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("user_id") or user_payload.get("sub")

    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id or schema_id")

    # ✅ New role check
    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    task_data.created_by = uuid.UUID(user_id)

    service = TaskService(schema_id)
    updated = service.update_task(task_id, task_data)

    if updated:
        return {"message": "Task updated successfully"}

    raise HTTPException(status_code=404, detail="Task not found")





# delete specific task
@task_router.delete("/{task_id}", response_model=dict)
def delete_task(task_id: uuid.UUID, request: Request):
    user_payload = request.state.user
    role = user_payload.get("role")
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("user_id") or user_payload.get("sub")

    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id or schema_id")

    if not role or role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized user")

    service = TaskService(schema_id)
    deleted = service.delete_task(task_id, uuid.UUID(user_id))

    if deleted:
        return {"message": "Task deleted successfully"}

    raise HTTPException(status_code=404, detail="Task not found or not owned by user")


