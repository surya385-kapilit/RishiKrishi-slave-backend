from typing import List
from fastapi import APIRouter,Depends,HTTPException, Request
from fastapi.responses import JSONResponse
from app.Models.user_model import UserResponse, UsersListResponse
from app.repository import user_repo
from app.repository.user_repo import get_admin_dashboard_details, get_admin_name_by_id, get_all_users, get_user_by_id_service, get_user_dashboard_details, get_users_list, user_exists_by_email, user_exists_by_phone
from app.service.internal_service import create_user, delete_user_in_sentry, update_user_in_sentry, userAlreadyExists,create_user_in_sentry
from pydantic import BaseModel
from app.middleware.auth_middleware import get_db_connection
from fastapi import Query
admin_router=APIRouter(prefix="/api/admin",tags=["admin"])
user_router=APIRouter(prefix="/api/users",tags=["users"])

class UserCreate(BaseModel):
    email: str
    name: str
    role: str
    phone: str
    
class UserUpdate(BaseModel):
    name: str
    is_active: bool | None = None
    email: str | None = None
    role: str | None = None
    phone: str | None = None
    
# Create user endpoint    
@user_router.post("/create-user")
async def create_user(request: Request, payload: UserCreate):
    user_payload = request.state.user  # Set by AuthMiddleware

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Reject if the role is supervisor
    if user_payload.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="User is not allowed to access this resource")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Schema ID missing in token")

    # Extract JWT token to send to Sentry
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    jwt_token = auth_header.split(" ")[1]

    email = payload.email
    name = payload.name
    role = payload.role
    phone = payload.phone
    
    #  Validations
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
    if not email or not name or not role:
        raise HTTPException(status_code=400, detail="Email, name, and role are required")
    role = role.upper()
    if role.upper() not in ["ADMIN", "SUPERVISOR", "MANAGER"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    #  Check if user already exists in tenant DB

    try:
        with get_db_connection(schema_id) as db_cursor:
            if user_exists_by_email(email, db_cursor) or user_exists_by_phone(phone, db_cursor):
                raise HTTPException(status_code=400, detail="User already exists with this email or phone")
    except HTTPException as http_err:
        #  Reraise 400 error as-is
        raise http_err
    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(status_code=500, detail="Internal server error while checking user existence")

    #  Create user in Sentry
    user_data = {
        "email": email,
        "name": name,
        "role": role,
        "phone": phone
    }

    sentry_response = create_user_in_sentry(user_data, jwt_token)
    if not sentry_response:
        raise HTTPException(status_code=500, detail="Failed to create user in Sentry")

    user_id = sentry_response.get("user_id")
    if not user_id:
        raise HTTPException(status_code=500, detail="user_id not returned from Sentry")

    #  Insert user into tenant schema
    try:
        with get_db_connection(schema_id) as db_cursor:
            db_cursor.execute("""
                INSERT INTO users (user_id, email, full_name, role, phone)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, email, name, role, phone))
    except Exception as e:
        print("DB insert failed:", e)
        raise HTTPException(status_code=500, detail="User created in Sentry but failed in tenant DB")

    return JSONResponse(
        status_code=201,
        content={
            "detail": "User created successfully in two servers",
            "user_id": user_id,
            "email": email,
            "name": name,
            "role": role,
            "phone": phone
        }
    )

#Get User-list
@user_router.get("/list", response_model=List[UsersListResponse])
async def get_user_list(request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if user_payload.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="User is not allowed to access this resource")
    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Schema ID missing in token")
    try:
        with get_db_connection(schema_id) as db_cursor:
            users=get_users_list(db_cursor)
            return users            
    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving users")  


#Get the user dashboard details
@user_router.get("/dashboard")
async def get_user_dashboard(request: Request):
    user_payload = request.state.user
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    schema_id = user_payload.get("schema_id")
    user_id = user_payload.get("sub")
    if not schema_id or not user_id:
        raise HTTPException(status_code=400, detail="Schema ID or User ID missing in token")
    user_dashboard_data = get_user_dashboard_details(schema_id, user_id)
    return JSONResponse(
        status_code=200,
        content={
            "message": "User dashboard data retrieved successfully",
            "data": user_dashboard_data
        }
    )


#Get All users For particular schema
@user_router.post("/")
async def get_auth(request: Request):
    user_router = request.state.user
    return {"user": user_router}

# Get all users endpoint in admin side
@user_router.get("/")
async def get_all_users_endpoint(
    request: Request,
    user_type: str = Query("all", enum=["all", "admins", "supervisors"]),
    page: int = 0,
    limit: int = 10
):
    user_payload = request.state.user  # Set by AuthMiddleware

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Only ADMIN can access
    if user_payload.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="User is not allowed to access this resource")

    schema_id = user_payload.get("schema_id")
    current_user_id = user_payload.get("sub")

    if not schema_id or not current_user_id:
        raise HTTPException(status_code=400, detail="Schema ID or User ID missing in token")

    try:
        with get_db_connection(schema_id) as db_cursor:
            users, total_users = get_all_users(db_cursor, user_type, current_user_id, page, limit)
            return JSONResponse(
                status_code=200,
                content={
                    "detail": "Users retrieved successfully",
                    "page": page,
                    "limit": limit,
                    "total_users": total_users,
                    "total_pages": (total_users + limit - 1) // limit,
                    "users": users
                }
            )
    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving users")
    
# User update endpoint admin an the user himself
@user_router.put("/{user_id}")
async def update_user_endpoint(request: Request, user_id: str, payload: UserUpdate):
    user_payload = request.state.user  # Set by AuthMiddleware

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    current_role = user_payload.get("role")
    current_user_id = user_payload.get("sub")
    schema_id = user_payload.get("schema_id")

    if not schema_id:
        raise HTTPException(status_code=400, detail="Schema ID missing in token")

    # Extract JWT token for Sentry API calls
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    jwt_token = auth_header.split(" ")[1]

    # Check permissions:
    # - Admin can update anyone
    # - Non-admin can only update their own profile and not modify role/status/email
    if current_role != "ADMIN" and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")

    # Prepare update data
    user_data = {"name": payload.name}
    status = None
    if payload.is_active is not None:
        status = "active" if payload.is_active else "inactive"
        user_data["is_active"] = payload.is_active

    # Restrict fields for non-admin users
    if current_role == "ADMIN":
        if payload.email:
            user_data["email"] = payload.email
        if payload.role:
            if payload.role.upper() not in ["ADMIN", "SUPERVISOR"]:
                raise HTTPException(status_code=400, detail="Invalid role")
            user_data["role"] = payload.role
        if payload.phone:
            user_data["phone"] = payload.phone
    else:
        # Normal users cannot change email, role, or active status
        if payload.email or payload.role or payload.is_active is not None:
            raise HTTPException(status_code=403, detail="You cannot modify email, role, or status")
        if payload.phone:
            user_data["phone"] = payload.phone

    # Check if user exists in tenant DB
    try:
        with get_db_connection(schema_id) as db_cursor:
            db_cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            if not db_cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found in tenant users")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(status_code=500, detail="Internal server error while checking user existence")

    # Update user in Sentry (Admin updates or user updating themselves)
    sentry_response = update_user_in_sentry(user_id, user_data, jwt_token)
    if not sentry_response:
        raise HTTPException(status_code=500, detail="Failed to update user in Sentry")

    # Update user in tenant schema DB
    try:
        with get_db_connection(schema_id) as db_cursor:
            query = "UPDATE users SET full_name = %s"
            params = [payload.name]
            if status:
                query += ", status = %s"
                params.append(status)
            if current_role == "ADMIN":
                if "email" in user_data:
                    query += ", email = %s"
                    params.append(user_data["email"])
                if "role" in user_data:
                    query += ", role = %s"
                    params.append(user_data["role"])
            if "phone" in user_data:
                query += ", phone = %s"
                params.append(user_data["phone"])
            query += " WHERE user_id = %s"
            params.append(user_id)
            db_cursor.execute(query, params)
    except Exception as e:
        print("DB update failed:", e)
        raise HTTPException(status_code=500, detail="User updated in Sentry but failed in tenant DB")

    return JSONResponse(
        status_code=200,
        content={
            "detail": "User updated successfully",
            # "user_id": user_id,
            # **user_data
        }
    )


# User delete endpoint admin only
@user_router.delete("/{user_id}")
async def delete_user_endpoint(request: Request, user_id: str):
    user_payload = request.state.user  # Set by AuthMiddleware

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Schema ID missing in token")

    # Extract JWT token to send to Sentry
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    jwt_token = auth_header.split(" ")[1]

    # Check if user exists in tenant DB
    try:
        with get_db_connection(schema_id) as db_cursor:
            db_cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            if not db_cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found in tenant")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(status_code=500, detail="Internal server error while checking user existence")

    # Delete user from Sentry
    sentry_response = delete_user_in_sentry(user_id, jwt_token)
    if not sentry_response:
        raise HTTPException(status_code=500, detail="Failed to delete user in Sentry")

    # Delete user from tenant schema
    try:
        with get_db_connection(schema_id) as db_cursor:
            db_cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    except Exception as e:
        print("DB delete failed:", e)
        raise HTTPException(status_code=500, detail="User deleted in Sentry but failed in tenant DB")

    return JSONResponse(
        status_code=200,
        content={"detail": "User deleted successfully", "user_id": user_id}
    )

# get user by id endpoint
@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_userid(request: Request, user_id: str):
    user_payload = request.state.user  # From AuthMiddleware
    current_role = user_payload.get("role")
    current_user_id = user_payload.get("sub")

    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if current_role != "ADMIN" and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to see this profile")
    
    schema_id = user_payload.get("schema_id")
    admin_name = get_admin_name_by_id(schema_id)  
    if not schema_id:
        raise HTTPException(status_code=400, detail="Schema ID missing in token")

    user_dict = get_user_by_id_service(user_id, schema_id, admin_name)

    return JSONResponse(
        status_code=200,
        content={"message": "User retrieved successfully", "user": user_dict}) 
    
# Get Admin Dashboard data
@admin_router.get("/dashboard")
async def get_admin_dashboard_data(request: Request):
    user_payload = request.state.user  # From AuthMiddleware
    if not user_payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if user_payload.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    schema_id = user_payload.get("schema_id")
    if not schema_id:
        raise HTTPException(status_code=400, detail="Schema ID missing in token")
    dashboard_data=get_admin_dashboard_details(schema_id)
    return JSONResponse(
        status_code=200,
        content={"message": "Admin dashboard data retrieved successfully", "data": dashboard_data}
    )
    

    
 


    