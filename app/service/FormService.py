from datetime import datetime
import json
import math
from typing import Any, Dict, List
import uuid

from fastapi import HTTPException
from app.Models.form_model import (
    FieldOption,
    FormCreate,
    FormFieldsResponse,
    FormResponse,
    FormResponseWithFields,
    GetAllFormsResponse,
)
from app.configuration.database import get_db_connection
from app.repository.user_repo import get_user_by_id


class FormService:
    def __init__(self, schema_id: str):
        self.schema_id = schema_id

    def create_form(self, form_data: FormCreate) -> FormResponse:
        form_id = uuid.uuid4()
        created_at = datetime.now()
        task_id = form_data.task_id
        if task_id:
            # Verify task exists
            with get_db_connection(self.schema_id) as cursor:
                cursor.execute("SELECT 1 FROM task WHERE task_id = %s", (str(task_id),))
                task_exists = cursor.fetchone()
                if not task_exists:
                    raise HTTPException(status_code=404, detail="Task not found")
        with get_db_connection(self.schema_id) as cursor:
            # Insert form
            cursor.execute(
                """
                INSERT INTO form 
                (form_id, task_id, title, description, created_by, created_at,is_active)
                VALUES (%s, %s, %s, %s, %s, %s,%s)
                """,
                (
                    str(form_id),
                    str(form_data.task_id),
                    form_data.title,
                    form_data.description,
                    str(form_data.created_by),
                    created_at,
                    True,
                ),
            )

            created_by = (
                get_user_by_id(str(form_data.created_by), cursor)
                if form_data.created_by
                else None
            )
            created_by_name = created_by["name"] if created_by else None
            form_data.created_by = created_by_name

            fields: List[FieldOption] = []
            for field in form_data.fields:
                field_id = uuid.uuid4()

                field_options_json = (
                    json.dumps(field.field_options) if field.field_options else None
                )

                cursor.execute(
                    """
                    INSERT INTO form_fields 
                    (field_id, form_id, name, field_type, is_required, field_options)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(field_id),
                        str(form_id),
                        field.name,
                        field.field_type,
                        field.is_required,
                        field_options_json,
                    ),
                )

                fields.append(field)

        return FormResponse(
            form_id=form_id,
            task_id=form_data.task_id,
            title=form_data.title,
            description=form_data.description,
            created_by=form_data.created_by,
            created_at=created_at,
            fields=fields,
        )

    # Update forms
    def update_form(self, form_id: str, form_data: FormCreate) -> FormResponse:
        updated_at = datetime.now()

        with get_db_connection(self.schema_id) as cursor:
            # Get original created_at
            cursor.execute(
                "SELECT created_at FROM form WHERE form_id = %s", (str(form_id),)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Form not found")
            original_created_at = row[0]

            #check if task_id exists
            if form_data.task_id:
                cursor.execute("SELECT 1 FROM task WHERE task_id = %s", (str(form_data.task_id),))
                task_exists = cursor.fetchone()
                if not task_exists:
                    raise HTTPException(status_code=404, detail="Task not found")

            # Update form basic info
            cursor.execute(
                """
                UPDATE form
                SET title = %s,
                    description = %s,
                    task_id = %s
                WHERE form_id = %s
                """,
                (
                    form_data.title,
                    form_data.description,
                    str(form_data.task_id),
                    str(form_id),
                ),
            )

            # Remove old fields
            cursor.execute(
                "DELETE FROM form_fields WHERE form_id = %s", (str(form_id),)
            )

            # Get created_by name
            created_by = (
                get_user_by_id(str(form_data.created_by), cursor)
                if form_data.created_by
                else None
            )
            created_by_name = created_by["name"] if created_by else None
            form_data.created_by = created_by_name

            # Insert updated fields
            fields: List[FieldOption] = []
            for field in form_data.fields:
                field_id = uuid.uuid4()
                field_options_json = (
                    json.dumps(field.field_options) if field.field_options else None
                )
                cursor.execute(
                    """
                    INSERT INTO form_fields
                    (field_id, form_id, name, field_type, is_required, field_options)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(field_id),
                        str(form_id),
                        field.name,
                        field.field_type,
                        field.is_required,
                        field_options_json,
                    ),
                )
                fields.append(field)

        return FormResponse(
            form_id=form_id,
            task_id=form_data.task_id,
            title=form_data.title,
            description=form_data.description,
            created_by=form_data.created_by,
            created_at=original_created_at,
            fields=fields,
        )

    # Get form with fields
    def get_form(self, form_id: str) -> FormResponseWithFields:
        with get_db_connection(self.schema_id) as cursor:
            # Fetch form details
            cursor.execute(
                """
                SELECT form_id, task_id, title, description, created_by, created_at
                FROM form
                WHERE form_id = %s
                """,
                (str(form_id),),
            )
            form_row = cursor.fetchone()
            if not form_row:
                raise ValueError("Form not found")

            # Fetch form fields
            cursor.execute(
                """
                SELECT name, field_type,field_id, is_required, field_options
                FROM form_fields
                WHERE form_id = %s
                """,
                (str(form_id),),
            )
            field_rows = cursor.fetchall()

        fields: List[FieldOption] = []
        for row in field_rows:
            field_options_data = row[4]
            if isinstance(field_options_data, str):
                field_options_data = json.loads(field_options_data)
            fields.append(
                FieldOption(
                    
                    name=row[0],
                    field_type=row[1],
                    field_id=row[2],
                    is_required=row[3],
                    field_options=field_options_data,
                )
            )

        return FormResponseWithFields(
            form_id=form_row[0],
            task_id=form_row[1],
            title=form_row[2],
            description=form_row[3],
            created_by=form_row[4],
            created_at=form_row[5],
            fields=fields,
        )

    # Get form fields only
    def get_form_fields(self, form_id: str) -> FormFieldsResponse:
        with get_db_connection(self.schema_id) as cursor:
            # Fetch form details
            cursor.execute(
                """
                SELECT form_id, task_id, title, description, created_by, created_at
                FROM form
                WHERE form_id = %s
                """,
                (str(form_id),),
            )
            form_row = cursor.fetchone()
            if not form_row:
                raise ValueError("Form not found")

            # Fetch form fields
            cursor.execute(
                """
                SELECT field_id, name, field_type, is_required, field_options
                FROM form_fields
                WHERE form_id = %s
                """,
                (str(form_id),),
            )
            field_rows = cursor.fetchall()
            # print("fields", field_rows)

        fields: List[FieldOption] = []
        for row in field_rows:
            field_options_data = row[4]
            if isinstance(field_options_data, str):
                field_options_data = json.loads(field_options_data)
            fields.append(
                FieldOption(
                    field_id=row[0],
                    name=row[1],
                    field_type=row[2],
                    is_required=row[3],
                    field_options=field_options_data,
                )
            )

        return FormFieldsResponse(
            form_id=form_row[0],
            # task_id=form_row[1],
            # title=form_row[2],
            # description=form_row[3],
            # created_by=form_row[4],
            # created_at=form_row[5],
            fields=fields,
        )

    # Delete form and its fields
    def delete_form(self, form_id: str) -> bool:
        with get_db_connection(self.schema_id) as cursor:
            # First check if form exists
            cursor.execute(
                "SELECT form_id FROM form WHERE form_id = %s", (str(form_id),)
            )
            form_exists = cursor.fetchone()
            if not form_exists:
                raise ValueError("Form not found or already deleted")

            # Delete fields first
            cursor.execute(
                "DELETE FROM form_fields WHERE form_id = %s", (str(form_id),)
            )
            # Delete form
            cursor.execute(
                "DELETE FROM form WHERE form_id = %s RETURNING form_id", (str(form_id),)
            )
            deleted = cursor.fetchone()
            if not deleted:
                raise ValueError("Form deletion failed")
        return True

    # Delete specific field
    def delete_form_field(self, form_id: str, field_id: str) -> bool:
        with get_db_connection(self.schema_id) as cursor:
            # First check if form exists
            cursor.execute(
                "SELECT form_id FROM form WHERE form_id = %s", (str(form_id),)
            )
            form_exists = cursor.fetchone()
            if not form_exists:
                raise ValueError("Form not found")

            # Delete specific field
            cursor.execute(
                """
                DELETE FROM form_fields
                WHERE form_id = %s AND field_id = %s
                RETURNING field_id
                """,
                (str(form_id), str(field_id)),
            )
            deleted = cursor.fetchone()
            if not deleted:
                raise ValueError("Field not found in this form")
        return True
    #Get forms-list by task
    def get_forms_list_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        with get_db_connection(self.schema_id) as cursor:
            # Check if task exists
            cursor.execute("SELECT 1 FROM task WHERE task_id = %s", (str(task_id),))
            task_exists = cursor.fetchone()
            if not task_exists:
                raise HTTPException(status_code=404, detail="Task not found")

            # Fetch forms for the task
            cursor.execute(
                """
                SELECT f.form_id, f.task_id, f.title ,is_active
                FROM form f
                JOIN users u ON f.created_by = u.user_id
                WHERE f.task_id = %s
                ORDER BY f.title ASC
                """,
                (str(task_id),),
            )
            forms = cursor.fetchall()

        form_list = [
            {
                "form_id": str(f[0]),
                "title": f[2],
                "is_active": f[3],

            }
            for f in forms
        ]
        return form_list


    # Get forms by task with pagination
    def get_forms_by_task(self, task_id: str, page: int = 0, limit: int = 10) -> dict:
        offset = page * limit
        with get_db_connection(self.schema_id) as cursor:
            # Check if task exists
            cursor.execute("SELECT 1 FROM task WHERE task_id = %s", (str(task_id),))
            task_exists = cursor.fetchone()
            if not task_exists:
                raise HTTPException(status_code=404, detail="Task not found")
            # Get total count for pagination
            cursor.execute(
                "SELECT COUNT(*) FROM form WHERE task_id = %s",
                (str(task_id),),
            )
            total_count = cursor.fetchone()[0]
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

            #  Fetch paginated forms
            cursor.execute(
                """
                SELECT f.form_id, f.task_id, f.title, f.description, u.full_name AS created_by_name, f.created_at ,f.is_active
                FROM form f
                JOIN users u ON f.created_by = u.user_id
                WHERE f.task_id = %s
                ORDER BY f.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (str(task_id), limit, offset),
            )
            forms = cursor.fetchall()

        form_list = [
            GetAllFormsResponse(
                form_id=f[0],
                task_id=f[1],
                title=f[2],
                description=f[3],
                created_by=f[4],
                created_at=f[5],
                is_active=f[6],
            )
            for f in forms
        ]

        return {
            "page": page,
            "limit": limit,
            "total_forms": total_count,
            "total_pages": total_pages,
            "forms": form_list,
        }

    # update status of the form like is_active status
    def update_form_status(self, form_id: str, updated_by: str):
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute("SELECT is_active FROM form WHERE form_id = %s", (form_id,))
            result = cursor.fetchone()
            if not result:
                raise Exception("Form not found")

            current_status = result[0]
            new_status = not current_status  # Flip the status

            # Update with the flipped status
            cursor.execute(
                """
                UPDATE form 
                SET is_active = %s 
                WHERE form_id = %s
                """,
                (new_status, form_id),
            )
            if cursor.rowcount == 0:
                raise Exception("Form not found")

        return {
            "message": "Status updated successfully",
            "form_id": form_id,
            "is_active": new_status,
        }
