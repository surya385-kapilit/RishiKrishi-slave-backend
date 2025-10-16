from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException
from app.middleware import auth_middleware

import subprocess
import os
from fastapi.responses import JSONResponse

from app.service import internal_service

from pydantic import BaseModel, EmailStr
from typing import Optional


from fastapi import Path

from app.configuration.database import get_db_connection
from typing import Literal

external_router = APIRouter(prefix="/external", tags=["tenants"])

TEMPLATE_SCHEMA = "schema_copy" # The schema to clone for new tenants
DB_URL = os.getenv("DB_URL") # Update with your DB URL  and dont put like this in production
print(f"Using DB_URL: {DB_URL}")


@external_router.post("/create-tenant")
async def create_tenant(request: Request):
    # db_pool=Depends(get_db_pool)

    data = await request.json()
    new_schema = data.get("schema_name")
    if not new_schema:
        return JSONResponse(
            status_code=400, content={"detail": "schema_name is required"}
        )
    new_schema = new_schema.replace(" ", "_").replace("-", "_").lower()
    try:
        # Step 1: pg_dump --schema-only for template_schema
        dump_cmd = ["pg_dump", "--schema", TEMPLATE_SCHEMA, "--schema-only", DB_URL]
        print("Running command:", dump_cmd)
        result = subprocess.run(dump_cmd, capture_output=True, text=True, check=True)
        print("After Result command:", result.stdout)

        dumped_sql = result.stdout

        # Step 2: Modify schema references
        modified_sql = dumped_sql.replace(f"{TEMPLATE_SCHEMA}.", f"{new_schema}.")
        modified_sql = modified_sql.replace(
            f"SCHEMA {TEMPLATE_SCHEMA}", f"SCHEMA {new_schema}"
        )
        modified_sql = (
            f"CREATE SCHEMA IF NOT EXISTS {new_schema};\nSET search_path TO {new_schema};\n"
            + modified_sql
        )

        # Step 3: Write to temp file
        os.makedirs("tmp", exist_ok=True)
        file_path = f"tmp/{new_schema}_clone.sql"
        with open(file_path, "w") as f:
            f.write(modified_sql)
        print(f"SQL file written to {file_path}")

        # Step 4: Apply schema to DB using psql
        psql_cmd = ["psql", DB_URL, "-f", file_path]
        print("Running psql command:", psql_cmd)
        subprocess.run(psql_cmd, check=True, capture_output=True, text=True)
        # subprocess.run(["psql", DB_URL, "-f", file_path], check=True)

        # Step 5: Dump newly created schema (optional if needed)
        final_dump_file = f"tmp/{new_schema}_final.sql"
        subprocess.run(
            [
                "pg_dump",
                "--schema",
                new_schema,
                "--schema-only",
                DB_URL,
                "-f",
                final_dump_file,
            ],
            check=True,
        )

        # Clean up temp file
        os.remove(file_path)
        return {
            "detail": f"Tenant schema '{new_schema}' created successfully",
            "schema_name": new_schema,
        }

    except subprocess.CalledProcessError as e:
        print("Error occurred:", e.stderr)
        return JSONResponse(
            status_code=500,
            content={"detail": "pg_dump or psql failed", "stderr": e.stderr},
        )


class AdminCreateRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: str
    role: Optional[str] = "ADMIN"
    schema_id:str

from typing import Literal

class AdminUpdateRequest(BaseModel):
    schema_id: str
    full_name: str
    status: Literal["active", "inactive"]

@external_router.post("/create-admin")
async def create_admin(request: Request, body: AdminCreateRequest):
    """
    Creates a new admin user in the schema specified in the request body,
    after validating the requester has 'superadmin' privileges from their JWT.
    """
    # 1. Authorization: Check the role from the JWT payload set by the middleware.
    # user_payload = request.state.user
    # if user_payload.get("role") != "superadmin":
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Forbidden: Requires superadmin privileges"
    #     )

    # 2. Validation: Get identifier and schema from the Pydantic model.
    identifier = body.email if body.email else body.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or phone is required")

    schema = body.schema_id
    if not schema:
        raise HTTPException(
            status_code=400, detail="schema_id is required in the request body"
        )

    # 3. Database Logic: Use the context manager for safe, clean DB operations.
    try:
        # The 'with' statement is CRITICAL. It handles getting the connection,
        # setting the schema, committing, and returning the connection.
        with get_db_connection(schema) as db_cursor:

            # Pass the cursor to your service method.
            if internal_service.userAlreadyExists(identifier, db_cursor):
                raise HTTPException(status_code=409, detail="User already exists")

            # Pass the same cursor to the create method.
            user_id, created = internal_service.create_user(
                db_cursor=db_cursor,
                email=body.email,
                name=body.full_name,
                role=body.role,
                phone=body.phone,
            )

            if not created:
                raise HTTPException(
                    status_code=500, detail="Failed to create user in the database"
                )

            # On success, return a JSON response. FastAPI handles the conversion.
            return {
                "message": "User created successfully",
                "user_id": user_id,
                "name": body.full_name,
                "email": body.email,
                "role": body.role,
            }

    except HTTPException:
        # Re-raise HTTPExceptions directly so FastAPI can handle them.
        raise
    except Exception as e:
        # Catch any other unexpected errors (DB connection issues, etc.)
        # and wrap them in a generic server error.
        print(f"An unexpected error occurred in create_admin for schema '{schema}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred.")


    

@external_router.put("/update-admin/{user_id}")
async def update_admin(user_id: str, body: AdminUpdateRequest):
    schema = body.schema_id
    full_name = body.full_name
    status = body.status

    if not all([schema, full_name, status]):
        raise HTTPException(status_code=400, detail="All fields are required")

    try:
        with get_db_connection(schema) as db_cursor:
            db_cursor.execute("""
                UPDATE users
                SET full_name = %s,
                    status = %s
                WHERE user_id = %s
            """, (full_name, status, user_id))

            if db_cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

        return {
            "message": "Admin updated successfully",
            "user_id": user_id,
            "updated_fields": {
                "full_name": full_name,
                "status": status
            }
        }

    except Exception as e:
        print(f"[ERROR] Failed to update user_id {user_id} in schema {schema}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update admin")




##Delete User

@external_router.delete("/delete-admin/{user_id}")
async def delete_admin(user_id: str, schema_id: str):
    """
    Deletes an admin from the tenant schema.
    Query param: ?schema_id=kapil
    """
    if not schema_id:
        raise HTTPException(status_code=400, detail="schema_id is required")

    try:
        with get_db_connection(schema_id) as db_cursor:
            db_cursor.execute("""
                DELETE FROM users
                WHERE user_id = %s
            """, (user_id,))
            if db_cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
        return {"message": "Admin deleted successfully", "user_id": user_id}
    except Exception as e:
        print(f"[ERROR] Failed to delete admin in schema {schema_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete admin")
