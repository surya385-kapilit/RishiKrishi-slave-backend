import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.Models.AccessToForm import FormAccessCreate, FormAccessResponse
from app.configuration.database import get_db_connection


class FormAccessService:
    def __init__(self, schema_id: str):
        self.schema_id = schema_id

    def create_access(
        self, access_data: FormAccessCreate, created_by: str
    ) -> Dict[str, Any]:
        created_at = datetime.now()
        responses: List[FormAccessResponse] = []
        skipped: List[str] = []
        notifications_created: List[Dict] = []

        with get_db_connection(self.schema_id) as cursor:
            try:
                # conn.autocommit = False

                # ✅ Get admin name for notification
                cursor.execute(
                    "SELECT full_name FROM users WHERE user_id = %s",
                    (str(created_by),),
                )
                admin_record = cursor.fetchone()
                admin_name = admin_record[0] if admin_record else "Admin"

                # ✅ Validate form
                cursor.execute(
                    "SELECT title FROM form WHERE form_id = %s",
                    (str(access_data.form_id),),
                )
                form_record = cursor.fetchone()
                if not form_record:
                    raise HTTPException(status_code=404, detail="Form not found")
                form_name = form_record[0]

                # ==============================
                # CASE 1: ACCESS TO ALL USERS
                # ==============================
                if access_data.access_type == "all":
                    cursor.execute(
                        "SELECT 1 FROM form_access WHERE form_id = %s AND user_id IS NULL",
                        (str(access_data.form_id),),
                    )
                    if cursor.fetchone():
                        skipped.append("Form already assigned to all users")
                    else:
                        access_id = uuid.uuid4()
                        cursor.execute(
                            """
                                INSERT INTO form_access 
                                (access_id, form_id, user_id, access_type, created_at, created_by)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                            (
                                str(access_id),
                                str(access_data.form_id),
                                None,
                                access_data.access_type,
                                created_at,
                                str(created_by),
                            ),
                        )
                        responses.append(
                            FormAccessResponse(
                                access_id=access_id,
                                form_id=access_data.form_id,
                                user_id=None,
                                access_type=access_data.access_type,
                                created_by=created_by,
                                created_at=created_at,
                            )
                        )

                        # ✅ Single broadcast notification
                        cursor.execute(
                            """
                                INSERT INTO notifications 
                                (user_id, title, message,created_at, created_by,form_id)
                                VALUES (
                                    NULL,
                                    'New Form Assigned',
                                    %s,
                                    %s,
                                    %s,
                                    %s
                                )
                                """,
                            (
                                f"'{admin_name}' has assigned '{form_name}' form to all users",
                                created_at,
                                str(created_by),
                                str(access_data.form_id),
                            ),
                        )
                        notifications_created.append(
                            {
                                "type": "all_users",
                                "message": "Broadcast notification created for all users",
                            }
                        )

                # ==============================
                # CASE 2: INDIVIDUAL ACCESS
                # ==============================
                else:
                    if not access_data.user_ids:
                        raise HTTPException(
                            status_code=400,
                            detail="user_ids required for individual access",
                        )

                    for user_id in access_data.user_ids:
                        cursor.execute(
                            "SELECT full_name FROM users WHERE user_id = %s",
                            (str(user_id),),
                        )
                        user_record = cursor.fetchone()
                        if not user_record:
                            skipped.append(f"User {user_id} not found")
                            continue

                        user_name = user_record[0]

                        cursor.execute(
                            "SELECT 1 FROM form_access WHERE form_id = %s AND user_id = %s",
                            (str(access_data.form_id), str(user_id)),
                        )
                        if cursor.fetchone():
                            skipped.append(f"Form already assigned to {user_name}")
                            continue

                        access_id = uuid.uuid4()
                        cursor.execute(
                            """
                                INSERT INTO form_access 
                                (access_id, form_id, user_id, access_type, created_at, created_by)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                            (
                                str(access_id),
                                str(access_data.form_id),
                                str(user_id),
                                access_data.access_type,
                                created_at,
                                str(created_by),
                            ),
                        )
                        responses.append(
                            FormAccessResponse(
                                access_id=access_id,
                                form_id=access_data.form_id,
                                user_id=user_id,
                                access_type=access_data.access_type,
                                created_by=created_by,
                                created_at=created_at,
                            )
                        )

                        # ✅ Individual notification
                        cursor.execute(
                            """
                                INSERT INTO notifications 
                                (user_id, title, message, created_at, created_by,form_id) 
                                VALUES (
                                    %s, 
                                    'New Form Assigned',
                                    %s,
                                    %s,
                                    %s,
                                    %s
                                )
                                """,
                            (
                                str(user_id),
                                f"'{admin_name}' has assigned '{form_name}' form to you",
                                created_at,
                                str(created_by),
                                str(access_data.form_id),
                            ),
                        )
                        notifications_created.append(
                            {
                                "type": "individual",
                                "user_id": str(user_id),
                                "user_name": user_name,
                                "message": f"Notification sent to {user_name}",
                            }
                        )

                # conn.commit()

            except Exception as e:
                # conn.rollback()
                raise e

        return {
            "success": responses,
            "skipped": skipped,
            "notifications_created": notifications_created,
        }

    def delete_access(
        self, form_id: str, user_id: Optional[str], deleted_by: str
    ) -> Dict[str, Any]:
        deleted_count = 0
        notifications_created = []

        with get_db_connection(self.schema_id) as cursor:
            try:
                # ✅ Get admin name
                cursor.execute(
                    "SELECT full_name FROM users WHERE user_id = %s", (deleted_by,)
                )
                admin_record = cursor.fetchone()
                admin_name = admin_record[0] if admin_record else "Admin"

                # ✅ Get form name
                cursor.execute("SELECT title FROM form WHERE form_id = %s", (form_id,))
                form_record = cursor.fetchone()
                if not form_record:
                    raise HTTPException(status_code=404, detail="Form not found")
                form_name = form_record[0]

                if user_id:
                    # ==============================
                    # CASE 1: DELETE INDIVIDUAL ACCESS
                    # ==============================
                    cursor.execute(
                        "SELECT full_name FROM users WHERE user_id = %s", (user_id,)
                    )
                    user_record = cursor.fetchone()
                    if not user_record:
                        raise HTTPException(status_code=404, detail="User not found")
                    user_name = user_record[0]

                    cursor.execute(
                        "DELETE FROM form_access WHERE form_id = %s AND user_id = %s RETURNING access_id",
                        (form_id, user_id),
                    )
                    deleted = cursor.fetchone()
                    if not deleted:
                        raise HTTPException(
                            status_code=404, detail="No access found for this user"
                        )

                    deleted_count += 1

                    # ✅ Notification for individual user
                    cursor.execute(
                        """
                        INSERT INTO notifications (user_id, title, message, created_at, created_by)
                        VALUES (%s, 'Form Access Removed', %s, %s, %s)
                        """,
                        (
                            user_id,
                            f"'{admin_name}' admin removed the form access for '{form_name}' form to you",
                            datetime.now(),
                            deleted_by,
                        ),
                    )

                    notifications_created.append(
                        {
                            "type": "individual",
                            "user_id": user_id,
                            "user_name": user_name,
                            "message": f"Notification sent to {user_name}",
                        }
                    )

                else:
                    # ==============================
                    # CASE 2: DELETE ALL ACCESS
                    # ==============================
                    cursor.execute(
                        "SELECT access_id FROM form_access WHERE form_id = %s AND user_id IS NULL",
                        (form_id,),
                    )
                    access_record = cursor.fetchone()
                    if not access_record:
                        raise HTTPException(
                            status_code=404,
                            detail="There is no form available to all user access",
                        )

                    cursor.execute(
                        "DELETE FROM form_access WHERE form_id = %s AND user_id IS NULL RETURNING access_id",
                        (form_id,),
                    )
                    deleted = cursor.fetchone()
                    if deleted:
                        deleted_count += 1

                        # ✅ Notification for broadcast
                        cursor.execute(
                            """
                            INSERT INTO notifications (user_id, title, message, created_at, created_by)
                            VALUES (NULL, 'Form Access Removed', %s, %s, %s)
                            """,
                            (
                                f"'{admin_name}' admin removed the form access for '{form_name}' form to all users",
                                datetime.now(),
                                deleted_by,
                            ),
                        )

                        notifications_created.append(
                            {
                                "type": "all_users",
                                "message": "Broadcast notification created for all users",
                            }
                        )

            except Exception as e:
                raise e

        return {
            "deleted_count": deleted_count,
            "notifications_created": notifications_created,
        }

    # get api
    def get_form_with_access(self, form_id: str = None):
        with get_db_connection(self.schema_id) as cursor:
            if form_id:
                cursor.execute(
                    """
                    SELECT f.form_id, f.title, f.description, f.created_by, f.created_at, f.is_active
                    FROM form f
                    WHERE f.form_id = %s
                    """,
                    (str(form_id),),
                )
                form_row = cursor.fetchone()
                if not form_row:
                    raise Exception(f"Form {form_id} not found")

                # fetch assigned users
                cursor.execute(
                    """
                    SELECT u.user_id, u.full_name as username
                    FROM form_access fa
                    JOIN users u ON fa.user_id = u.user_id
                    WHERE fa.form_id = %s
                    """,
                    (str(form_id),),
                )
                users = [
                    {"user_id": row[0], "username": row[1]} for row in cursor.fetchall()
                ]

                return {
                    "form_id": form_row[0],
                    "title": form_row[1],
                    "description": form_row[2],
                    "created_by": form_row[3],
                    "created_at": form_row[4],
                    "is_active": form_row[5],
                    "assigned_users": users,
                }

            else:
                # get all forms
                cursor.execute(
                    """
                    SELECT f.form_id, f.title, f.description, f.created_by, f.created_at, f.is_active
                    FROM form f
                    """
                )
                forms = cursor.fetchall()
                result = []
                for form_row in forms:
                    cursor.execute(
                        """
                        SELECT u.user_id, u.full_name as username
                        FROM form_access fa
                        JOIN users u ON fa.user_id = u.user_id
                        WHERE fa.form_id = %s
                        """,
                        (str(form_row[0]),),
                    )
                    users = [
                        {"user_id": row[0], "username": row[1]}
                        for row in cursor.fetchall()
                    ]
                    result.append(
                        {
                            "form_id": form_row[0],
                            "title": form_row[1],
                            "description": form_row[2],
                            "created_by": form_row[3],
                            "created_at": form_row[4],
                            "is_active": form_row[5],
                            "assigned_users": users,
                        }
                    )
                return result

    # get assigned form to user or supervisour
    def get_forms_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        forms = []

        with get_db_connection(self.schema_id) as cursor:
            try:
                # ✅ Fetch forms with individual access OR all-user access
                cursor.execute(
                    """
                    SELECT DISTINCT f.form_id, f.title, f.description, f.created_by, f.created_at, f.is_active
                    FROM form f
                    INNER JOIN form_access fa ON f.form_id = fa.form_id
                    WHERE f.is_active = TRUE
                    AND (
                            fa.user_id = %s 
                            OR fa.user_id IS NULL
                        )
                    """,
                    (user_id,),
                )

                records = cursor.fetchall()
                for row in records:
                    forms.append(
                        {
                            "form_id": row[0],
                            "title": row[1],
                            "description": row[2],
                            "created_by": row[3],
                            "created_at": row[4],
                            "is_active": row[5],
                        }
                    )
            except Exception as e:
                raise e

        return forms
