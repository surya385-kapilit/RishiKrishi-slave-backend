from typing import Any, Dict, Optional
from app.Models.notification import MarkReadResponse, NotificationCountResponse
from app.configuration.database import get_db_connection


class NotificationService:
    def __init__(self, schema_id: str):
        self.schema_id = schema_id

    def get_unread_count(self, user_id: str) -> NotificationCountResponse:
        with get_db_connection(self.schema_id) as cursor:
            # Now count distinct notifications
            cursor.execute(
                """
                SELECT COUNT(DISTINCT n.notification_id) AS unread_count
                FROM notifications n
                JOIN form_access fa ON n.form_id = fa.form_id
                JOIN users u ON u.user_id = %s
                WHERE (n.user_id = %s OR (fa.access_type = 'all' AND u.role <> 'ADMIN'))
                AND n.is_read = FALSE
                AND n.notification_id NOT IN (
                    SELECT notification_id 
                    FROM notification_reads 
                    WHERE user_id = %s
                )
                """,
                (user_id, user_id, user_id),
            )
            result = cursor.fetchone()
            print("DEBUG → Unread count for user:", user_id, "=", result[0])
            return NotificationCountResponse(user_id=user_id, unread_count=result[0])

    def mark_as_read(self, notification_id: int, user_id: str):
        with get_db_connection(self.schema_id) as cursor:
            # Step 1: Find form_id and access_type
            cursor.execute(
                """
                SELECT n.form_id, fa.access_type
                FROM notifications n
                LEFT JOIN form_access fa ON n.form_id = fa.form_id
                WHERE n.notification_id = %s
                """,
                (notification_id,),
            )
            row = cursor.fetchone()

            if not row:
                return {
                    "notification_id": notification_id,
                    "status": "error",
                    "message": "Notification not found",
                }
            form_id, access_type = row

            # ✅ Case 1: INDIVIDUAL → directly update notifications
            if access_type == "individual":
                cursor.execute(
                    "UPDATE notifications SET is_read = true WHERE notification_id = %s",
                    (notification_id,),
                )
                return {"status": "success", "message": "Marked as read (INDIVIDUAL)"}

            # ✅ Case 2: ALL → insert into notification_reads
            if access_type == "all":
                # First check if this user already inserted
                cursor.execute(
                    "SELECT 1 FROM notification_reads WHERE notification_id = %s AND user_id = %s",
                    (notification_id, user_id),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO notification_reads (notification_id, user_id) VALUES (%s, %s)",
                        (notification_id, user_id),
                    )

                # Now check if all non-admin users have read
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM users u 
                    WHERE u.role != 'ADMIN'
                    """
                )
                total_users = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT nr.user_id)
                    FROM notification_reads nr
                    JOIN users u ON nr.user_id = u.user_id
                    WHERE nr.notification_id = %s
                    AND u.role != 'ADMIN'
                    """,
                    (notification_id,),
                )
                read_users = cursor.fetchone()[0]

                if total_users > 0 and total_users == read_users:
                    # All non-admin users read → update and cleanup
                    cursor.execute(
                        "UPDATE notifications SET is_read = true WHERE notification_id = %s",
                        (notification_id,),
                    )
                    cursor.execute(
                        "DELETE FROM notification_reads WHERE notification_id = %s",
                        (notification_id,),
                    )

                # return {"status": "success", "message": "Marked as read (ALL)"}
                return {
                    "notification_id": notification_id,
                    "status": "success",
                    "message": "Marked as read (ALL)",
                }

    # def list_notifications(self, user_id: str, role: str, page: int, limit: int, status: Optional[str]) -> Dict[str, Any]:
    #     offset = (page - 1) * limit

    #     # Build WHERE condition for read/unread
    #     status_condition = ""
    #     if status == "unread":
    #         status_condition = " AND n.is_read = FALSE "
    #     elif status == "read":
    #         status_condition = " AND n.is_read = TRUE "

    #     with get_db_connection(self.schema_id) as cursor:
    #         # --- Count total ---
    #         if role.lower() == "admin":
    #             # ✅ Admins only see their own notifications
    #             cursor.execute(
    #                 f"""
    #                 SELECT COUNT(*)
    #                 FROM notifications n
    #                 WHERE n.user_id = %s {status_condition};
    #                 """,
    #                 (user_id,),
    #             )
    #         else:
    #             # ✅ Normal users see own + "all" access notifications
    #             cursor.execute(
    #                 f"""
    #                 SELECT COUNT(*) AS total_count FROM (
    #                     SELECT n.notification_id
    #                     FROM notifications n
    #                     WHERE n.user_id = %s {status_condition}

    #                     UNION ALL

    #                     SELECT n.notification_id
    #                     FROM notifications n
    #                     JOIN form_access fa ON fa.form_id = n.form_id
    #                     WHERE fa.access_type = 'all' {status_condition}
    #                 ) AS combined;
    #                 """,
    #                 (user_id,),
    #             )

    #         total_count = cursor.fetchone()[0]
    #         total_pages = (total_count + limit - 1) // limit

    #         # --- Fetch paginated notifications ---
    #         if role.lower() == "admin":
    #             cursor.execute(
    #                 f"""
    #                 SELECT
    #                     n.notification_id,
    #                     n.title,
    #                     n.message,
    #                     n.is_read,
    #                     n.created_at,
    #                     n.form_id,
    #                     f.title AS form_title,
    #                     'individual' AS access_type
    #                 FROM notifications n
    #                 LEFT JOIN form f ON n.form_id = f.form_id
    #                 WHERE n.user_id = %s {status_condition}
    #                 ORDER BY created_at DESC
    #                 LIMIT %s OFFSET %s;
    #                 """,
    #                 (user_id, limit, offset),
    #             )
    #         else:
    #             cursor.execute(
    #                 f"""
    #                 SELECT * FROM (
    #                     SELECT
    #                         n.notification_id,
    #                         n.title,
    #                         n.message,
    #                         n.is_read,
    #                         n.created_at,
    #                         n.form_id,
    #                         f.title AS form_title,
    #                         'individual' AS access_type
    #                     FROM notifications n
    #                     LEFT JOIN form f ON n.form_id = f.form_id
    #                     WHERE n.user_id = %s {status_condition}

    #                     UNION ALL

    #                     SELECT
    #                         n.notification_id,
    #                         n.title,
    #                         n.message,
    #                         n.is_read,
    #                         n.created_at,
    #                         n.form_id,
    #                         f.title AS form_title,
    #                         'all' AS access_type
    #                     FROM notifications n
    #                     JOIN form_access fa ON fa.form_id = n.form_id
    #                     LEFT JOIN form f ON n.form_id = f.form_id
    #                     WHERE fa.access_type = 'all' {status_condition}
    #                 ) AS combined
    #                 ORDER BY created_at DESC
    #                 LIMIT %s OFFSET %s;
    #                 """,
    #                 (user_id, limit, offset),
    #             )

    #         rows = cursor.fetchall()

    #         notifications = [
    #             {
    #                 "notification_id": row[0],
    #                 "title": row[1],
    #                 "message": row[2],
    #                 "is_read": row[3],
    #                 "created_at": row[4],
    #                 "form_id": row[5],
    #                 "form_title": row[6],
    #                 "access_type": row[7],
    #             }
    #             for row in rows
    #         ]

    #     return {
    #         "notifications": notifications,
    #         "pagination": {
    #             "total_count": total_count,
    #             "total_pages": total_pages,
    #             "current_page": page,
    #             "limit": limit,
    #             "next_page": page < total_pages,
    #             "previous_page": page > 1,
    #         },
    #     }

    def list_notifications(
        self, user_id: str, role: str, page: int, limit: int, status: Optional[str]
    ) -> Dict[str, Any]:
        offset = page * limit

        with get_db_connection(self.schema_id) as cursor:
            # --- Count total ---
            if role.lower() == "admin":
                base_query = """
                    SELECT COUNT(*) 
                    FROM notifications n
                    WHERE n.user_id = %s
                """
                params = [user_id]
                if status == "unread":
                    base_query += " AND n.is_read = FALSE"
                elif status == "read":
                    base_query += " AND n.is_read = TRUE"
            else:
                # Non-admin
                base_query = """
                    SELECT COUNT(*) 
                    FROM (
                        -- individual
                        SELECT n.notification_id, n.is_read
                        FROM notifications n
                        WHERE n.user_id = %s

                        UNION ALL

                        -- all
                        SELECT n.notification_id,
                            CASE WHEN EXISTS (
                                    SELECT 1 FROM notification_reads nr
                                    WHERE nr.notification_id = n.notification_id
                                    AND nr.user_id = %s
                            ) THEN TRUE ELSE FALSE END AS is_read
                        FROM notifications n
                        JOIN form_access fa ON fa.form_id = n.form_id
                        WHERE fa.access_type = 'all'
                    ) AS combined
                """
                params = [user_id, user_id]

                if status == "unread":
                    base_query += " WHERE combined.is_read = FALSE"
                elif status == "read":
                    base_query += " WHERE combined.is_read = TRUE"

            cursor.execute(base_query, params)
            total_count = cursor.fetchone()[0]
            total_pages = (total_count + limit - 1) // limit

            # --- Fetch paginated notifications ---
            if role.lower() == "admin":
                cursor.execute(
                    f"""
                    SELECT 
                        n.notification_id,
                        n.title,
                        n.message,
                        n.is_read,
                        n.created_at,
                        n.form_id,
                        f.title AS form_title,
                        'individual' AS access_type
                    FROM notifications n
                    LEFT JOIN form f ON n.form_id = f.form_id
                    WHERE n.user_id = %s
                    {"AND n.is_read = FALSE" if status == "unread" else ""}
                    {"AND n.is_read = TRUE" if status == "read" else ""}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s;
                    """,
                    (user_id, limit, offset),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT *
FROM (
    -- individual
    SELECT 
        n.notification_id,
        n.title,
        n.message,
        n.is_read,
        n.created_at,
        n.form_id,
        f.title AS form_title,
        'individual' AS access_type
    FROM notifications n
    LEFT JOIN form f ON n.form_id = f.form_id
    WHERE n.user_id = %s

    UNION ALL

    -- all
    SELECT 
        n.notification_id,
        n.title,
        n.message,
        CASE WHEN EXISTS (
            SELECT 1 FROM notification_reads nr
            WHERE nr.notification_id = n.notification_id
            AND nr.user_id = %s
        ) THEN TRUE ELSE FALSE END AS is_read,
        n.created_at,
        n.form_id,
        f.title AS form_title,
        'all' AS access_type
    FROM notifications n
    JOIN form_access fa ON fa.form_id = n.form_id
    LEFT JOIN form f ON n.form_id = f.form_id
    WHERE fa.access_type = 'all'
) AS combined
{ "WHERE combined.is_read = FALSE" if status == "unread" else "" }
{ "WHERE combined.is_read = TRUE" if status == "read" else "" }
ORDER BY created_at DESC
LIMIT %s OFFSET %s;
                    """,
                    (user_id, user_id, limit, offset),
                )

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
                }
                for row in rows
            ]

        return {
            "notifications": notifications,
            "pagination": {
                "total_notifications": total_count,
                "current_page": page,
                "limit": limit,
                "total_pages": total_pages,
                "next_page": page < total_pages,
                "previous_page": page > 1,
            },
        }
