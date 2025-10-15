from math import ceil
from typing import Any, Dict, Optional

from fastapi import HTTPException
from app.Models.notification import NotificationCountResponse
from app.configuration.database import get_db_connection


class NotificationService:
    def __init__(self, schema_id: str):
        self.schema_id = schema_id

    def get_unread_count(self, user_id: str) -> NotificationCountResponse:
        with get_db_connection(self.schema_id) as cursor:
            # Now count distinct notifications
            cursor.execute(
                """
                select count(user_id) as unread from notifications where is_read=false and user_id= %s

                """,
                (user_id,),
            )
            result = cursor.fetchone()
            print("DEBUG → Unread count for user:", user_id, "=", result[0])
            return NotificationCountResponse(user_id=user_id, unread_count=result[0])

    def mark_as_read(self, user_id: str):
        with get_db_connection(self.schema_id) as cursor:
            # cursor = conn.cursor()
            try:
                # ✅ Update only unread notifications for this user
                cursor.execute(
                    """
                    UPDATE notifications
                    SET is_read = true
                    WHERE user_id = %s AND is_read = false
                    """,
                    (user_id,),
                )
                updated_rows = cursor.rowcount  # Number of notifications updated
                # cursor.commit()

                if updated_rows > 0:
                    return {
                        "status": "success",
                        "message": f"{updated_rows} notification(s) marked as read",
                    }
                else:
                    return {
                        "status": "info",
                        "message": "No unread notifications found",
                    }

            except Exception as e:
                # cursor.rollback()
                raise e
            finally:
                cursor.close()

    # ✅ Get all notifications (read/unread/all) with pagination
    def list_notifications(
        self,
        user_id: str,
        role: str,
        page: int,
        limit: int,
        status: str = None,
    ):
        offset = page * limit

        with get_db_connection(self.schema_id) as cursor:
            try:
                base_query = """
                    SELECT n.notification_id, n.title, n.message, n.is_read, 
                           n.created_at, n.form_id, f.title AS form_title, 
                           fa.access_type, n.submission_id
                    FROM notifications n
                    LEFT JOIN form f ON n.form_id = f.form_id
                    LEFT JOIN form_access fa ON f.form_id = fa.form_id AND fa.user_id = n.user_id
                    WHERE n.user_id = %s
                """

                params = [user_id]

                # ✅ Filter by read/unread
                if status == "read":
                    base_query += " AND n.is_read = true"
                elif status == "unread":
                    base_query += " AND n.is_read = false"

                # ✅ Count total
                count_query = f"SELECT COUNT(*) FROM ({base_query}) AS total"
                cursor.execute(count_query, tuple(params))
                total_count = cursor.fetchone()[0]

                # ✅ Apply pagination
                base_query += " ORDER BY n.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cursor.execute(base_query, tuple(params))
                rows = cursor.fetchall()

                notifications = [
                    {
                        "notification_id": row[0],
                        "title": row[1],
                        "message": row[2],
                        "is_read": row[3],
                        "created_at": row[4],
                        "form_id": row[5],
                        "form_title": row[6],
                        "access_type": row[7],
                        "submission_id": row[8],
                    }
                    for row in rows
                ]

                total_pages = ceil(total_count / limit) if total_count > 0 else 1

                return {
                    "notifications": notifications,
                    "pagination": {
                        "total_notifications": total_count,
                        "current_page": page,
                        "limit": limit,
                        "total_pages": total_pages,
                        "next_page": page + 1 if (page + 1) < total_pages else None,
                        "previous_page": page - 1 if page > 0 else None,
                    },
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                cursor.close()