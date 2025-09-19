import math
from typing import List
import uuid

from app.Models.task_model import TaskCreate, TaskCreationResponse, TaskListResponse, TaskResponse, TaskUpdate
from app.configuration.database import get_db_connection
from app.repository.user_repo import get_user_by_id


class TaskService:
    def __init__(self, schema_id: str):
        self.schema_id = schema_id

    def create_task(self, task_data: TaskCreate) -> TaskCreationResponse:
        with get_db_connection(self.schema_id) as cursor:
            task_id = uuid.uuid4()
            cursor.execute(
                """
                INSERT INTO task (task_id, name, description, created_by)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    str(task_id),
                    task_data.name,
                    task_data.description,
                    str(task_data.created_by),
                ),
            )

            cursor.execute(
                """
                SELECT task_id, name, description, created_by, created_at
                FROM task
                WHERE task_id = %s
                """,
                (str(task_id),),
            )
            task_record = cursor.fetchone()

            created_by = get_user_by_id(task_record[3], cursor) if task_record else None
            created_by_name = created_by["name"] if created_by else None
            # print("Created by user details:", created_by)

            return TaskCreationResponse(
                task_id=task_record[0],
                name=task_record[1],
                description=task_record[2],
                created_by=created_by_name,
                created_at=task_record[4],
            )

    # update task with task_id
    def update_task(self, task_id: uuid.UUID, task_data: TaskUpdate) -> bool:
        with get_db_connection(self.schema_id) as cursor:
            result = cursor.execute(
                """
                UPDATE task
                SET name = %s,
                    description = %s,
                    created_by = %s
                WHERE task_id = %s
                """,
                (
                    task_data.name,
                    task_data.description,
                    str(task_data.created_by),
                    str(task_id),
                ),
            )
            # commit may be required depending on connection setup
            return cursor.rowcount == 1
    
    # get task by task_id
    def get_task_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskResponse | None:
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(
                """
                SELECT t.task_id, t.name, t.description, u.full_name AS created_by_name, 
                    t.created_at, COUNT(f.form_id) AS form_count
                FROM task t
                JOIN users u ON t.created_by = u.user_id
                LEFT JOIN form f ON t.task_id = f.task_id
                WHERE t.task_id = %s AND t.created_by = %s
                GROUP BY t.task_id, t.name, t.description, u.full_name, t.created_at
                """,
                (str(task_id), str(user_id)),
            )
            row = cursor.fetchone()
            if row:
                return TaskResponse(
                    task_id=row[0],
                    name=row[1],
                    description=row[2],
                    created_by=row[3],
                    created_at=row[4],
                    form_count=row[5]
                )
            return None
    #get all tasks
    def get_tasks_list(self, user_id: uuid.UUID) -> List[TaskResponse]:  
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(
                """
                SELECT t.task_id, t.name
                FROM task t
                JOIN users u ON t.created_by = u.user_id
                LEFT JOIN form f ON t.task_id = f.task_id
                WHERE t.created_by = %s
                GROUP BY t.task_id, t.name
                ORDER BY t.created_at DESC
                """,
                (str(user_id),),
            )
            rows = cursor.fetchall()
            tasks = [
                TaskListResponse(
                    task_id=row[0],
                    title=row[1]
                )
                for row in rows
            ]
            print("tasks", len(tasks))
            return tasks

    #get tasks list for user
    def get_tasks_list_for_user(self, user_id: uuid.UUID) -> List[TaskListResponse]:
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(
                """
                SELECT DISTINCT t.task_id, t.name
                FROM task t
                JOIN form f ON t.task_id = f.task_id
                JOIN form_access fa ON f.form_id = fa.form_id
                WHERE fa.user_id = %s OR fa.user_id IS NULL
                
                """,
                (str(user_id),),
            )
            rows = cursor.fetchall()
            tasks = [
                TaskListResponse(
                    task_id=row[0],
                    title=row[1]
                )
                for row in rows
            ]
            print("tasks", len(tasks))
            return tasks  

    
    # # get all tasks with pagination
        # def get_all_tasks(self, user_id: uuid.UUID, page: int = 0, limit: int = 10) -> dict[str, any]:
        #     offset = page * limit
        #     with get_db_connection(self.schema_id) as cursor:
        #         # Count total tasks for this user
        #         cursor.execute(
        #             "SELECT COUNT(*) FROM task WHERE created_by = %s", (str(user_id),)
        #         )
        #         total_count = cursor.fetchone()[0]
        #         total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

        #         # Fetch tasks with pagination
        #         cursor.execute(
        #             """
        #             SELECT t.task_id, t.name, t.description, u.full_name AS created_by_name, 
        #                t.created_at, COUNT(f.form_id) AS form_count
        #         FROM task t
        #         JOIN users u ON t.created_by = u.user_id
        #         LEFT JOIN form f ON t.task_id = f.task_id
        #         WHERE t.created_by = %s
        #         GROUP BY t.task_id, t.name, t.description, u.full_name, t.created_at
        #         ORDER BY t.created_at DESC
        #         LIMIT %s OFFSET %s
        #             """,
        #             (str(user_id), limit, offset),
        #         )
        #         rows = cursor.fetchall()
        #         tasks = [
        #             TaskResponse(
        #                 task_id=row[0],
        #                 name=row[1],
        #                 description=row[2],
        #                 created_by=row[3],
        #                 created_at=row[4],
        #                 form_count=row[5]
        #             )
        #             for row in rows
        #         ]

        #         # Return structured response
        #         return {
        #             "page": page,
        #             "limit": limit,
        #             "total_tasks": total_count,
        #             "total_pages": total_pages,
        #             "tasks": tasks,
        #         }
    # get all tasks with pagination (works for both admin and users)
    def get_all_tasks(self, user_id: uuid.UUID, role: str, page: int = 0, limit: int = 10) -> dict[str, any]:
        offset = page * limit

        with get_db_connection(self.schema_id) as cursor:
            if role.lower() == "admin":
                # Admin: tasks created by self
                cursor.execute(
                    "SELECT COUNT(*) FROM task WHERE created_by = %s", (str(user_id),)
                )
                total_count = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT t.task_id, t.name, t.description, u.full_name AS created_by_name,
                        t.created_at, COUNT(f.form_id) AS form_count
                    FROM task t
                    JOIN users u ON t.created_by = u.user_id
                    LEFT JOIN form f ON t.task_id = f.task_id
                    WHERE t.created_by = %s
                    GROUP BY t.task_id, t.name, t.description, u.full_name, t.created_at
                    ORDER BY t.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(user_id), limit, offset),
                )
            else:
                # Non-admin: tasks where user has form access
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT t.task_id)
                    FROM task t
                    JOIN form f ON t.task_id = f.task_id
                    JOIN form_access fa ON f.form_id = fa.form_id
                    WHERE fa.user_id = %s OR fa.user_id IS NULL
                    """,
                    (str(user_id),)
                )
                total_count = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT DISTINCT t.task_id, t.name, t.description, u.full_name AS created_by_name,
                                    t.created_at, COUNT(f.form_id) AS form_count
                    FROM task t
                    JOIN users u ON t.created_by = u.user_id
                    JOIN form f ON t.task_id = f.task_id
                    JOIN form_access fa ON f.form_id = fa.form_id
                    WHERE fa.user_id = %s OR fa.user_id IS NULL
                    GROUP BY t.task_id, t.name, t.description, u.full_name, t.created_at
                    ORDER BY t.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(user_id), limit, offset),
                )

            rows = cursor.fetchall()
            tasks = [
                TaskResponse(
                    task_id=row[0],
                    name=row[1],
                    description=row[2],
                    created_by=row[3],
                    created_at=row[4],
                    form_count=row[5]
                )
                for row in rows
            ]

            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
            return {
                "page": page,
                "limit": limit,
                "total_tasks": total_count,
                "total_pages": total_pages,
                "tasks": tasks,
            }



    # delete task by task_id
    def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(
                """
                DELETE FROM task
                WHERE task_id = %s AND created_by = %s
                """,
                (str(task_id), str(user_id)),
            )
            return cursor.rowcount == 1

    #get favorite tasks
    def get_tasks_by_ids(self, task_ids: List[uuid.UUID]) -> List[TaskResponse]:
            with get_db_connection(self.schema_id) as cursor:
                # convert UUIDs to strings
                task_ids_str = [str(tid) for tid in task_ids]

                cursor.execute(
                    """
                    SELECT 
                        t.task_id, 
                        t.name, 
                        t.description, 
                        u.full_name AS created_by_name, 
                        t.created_at,
                        COUNT(f.form_id) AS form_count
                    FROM task t
                    JOIN users u ON t.created_by = u.user_id
                    LEFT JOIN form f ON f.task_id = t.task_id
                    WHERE t.task_id = ANY(%s::uuid[])
                    GROUP BY t.task_id, u.full_name
                    """,
                    (task_ids_str,),  # ✅ pass list of strings instead of UUID objects
                )

                rows = cursor.fetchall()
                return [
                    TaskResponse(
                        task_id=row[0],
                        name=row[1],
                        description=row[2],
                        created_by=row[3],
                        created_at=row[4],
                        form_count=row[5],
                    )
                    for row in rows
                ]

