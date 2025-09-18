import asyncio
from datetime import datetime
import json
import logging
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime

from fastapi import HTTPException, UploadFile

from app.Models.form_submittions import FieldValue, FormSubmissionRequest, FormSubmissionResponse, FormUpdateRequest
from app.configuration.database import get_db_connection
from app.configuration.s3service import S3Service
logger = logging.getLogger(__name__)

class FormSubmissions:
    def __init__(self, schema_id: str):
        self.schema_id = schema_id

    # async def submit_form_with_files(
    #     self,
    #     form_id: str,
    #     submitted_by: str,
    #     field_values: List[FieldValue],
    #     files: Optional[List[UploadFile]],
    #     s3: S3Service,
    #     parsed_data: Optional[FormSubmissionRequest] = None,
    # ):
    #     """
    #     Save form submission and handle multiple file uploads for the same field_id using file_mappings.
    #     """
    #     with get_db_connection(self.schema_id) as cursor:
    #         # Map files to field_ids, allowing multiple files per field_id
    #         file_map = {}
    #         if files and parsed_data and parsed_data.file_mappings:
    #             # Validate file_mappings
    #             file_field_ids = {str(mapping.field_id) for mapping in parsed_data.file_mappings}
    #             field_ids = {str(fv.field_id) for fv in field_values}
                
    #             # Check if all mapped field_ids exist in field_values
    #             if not file_field_ids.issubset(field_ids):
    #                 raise HTTPException(
    #                     status_code=400,
    #                     detail="Some field_ids in file_mappings do not exist in field_values",
    #                 )

    #             # Check for duplicate file_indices
    #             file_indices = [mapping.file_index for mapping in parsed_data.file_mappings]
    #             if len(file_indices) != len(set(file_indices)):
    #                 raise HTTPException(
    #                     status_code=400,
    #                     detail="Duplicate file_index values in file_mappings",
    #                 )

    #             # Check if file_indices are valid
    #             max_index = len(files) - 1
    #             if any(mapping.file_index < 0 or mapping.file_index > max_index for mapping in parsed_data.file_mappings):
    #                 raise HTTPException(
    #                     status_code=400,
    #                     detail=f"Invalid file_index in file_mappings; must be between 0 and {max_index}",
    #                 )

    #             # Upload files concurrently
    #             upload_tasks = [s3.upload_file(files[mapping.file_index]) for mapping in parsed_data.file_mappings]
    #             uploaded_urls = await asyncio.gather(*upload_tasks, return_exceptions=True)

    #             # Map uploaded URLs to field_ids, allowing multiple URLs per field_id
    #             for mapping, url in zip(parsed_data.file_mappings, uploaded_urls):
    #                 if isinstance(url, Exception):
    #                     raise HTTPException(status_code=400, detail=f"File upload failed: {str(url)}")
    #                 field_id = str(mapping.field_id)
    #                 if field_id not in file_map:
    #                     file_map[field_id] = []
    #                 file_map[field_id].append(url)

    #             logger.debug(f"File map: {file_map}")

    #         # Merge file URLs into field_values
    #         final_field_values = []
    #         for fv in field_values:
    #             fid = str(fv.field_id)
    #             if fid in file_map:
    #                 # Store all URLs for this field as a JSON array in one row
    #                 final_field_values.append({
    #                     "field_id": fid,
    #                     "value": json.dumps(file_map[fid])  # Convert Python list to JSON string
    #                 })
    #             # Handle multiselect/checkbox fields (array values)
    #             elif isinstance(fv.value, list):
    #                 # Convert array to JSON string for storage
    #                 final_field_values.append({
    #                     "field_id": fid,
    #                     "value": json.dumps(fv.value)  # Store as JSON array string
    #                 })
    #             # Handle single values (strings, numbers, etc.)
    #             else:
    #                 final_field_values.append({
    #                     "field_id": fid,
    #                     "value": str(fv.value) if fv.value is not None else None
    #                 })
    #         logger.debug(f"Final field values: {final_field_values}")
    #         submission_id = str(uuid.uuid4())  # Generate UUID in Python
    #         # Insert into form_submissions and get submission time
    #         cursor.execute(
    #             """
    #             INSERT INTO form_submissions (submission_id, form_id, submitted_by, submitted_at)
    #             VALUES (%s, %s, %s, NOW())
    #             RETURNING submitted_at
    #             """,
    #             (submission_id, str(form_id), str(submitted_by)),
    #         )
    #         submitted_at = cursor.fetchone()[0]

    #         # Insert field values, supporting multiple rows for the same field_id
    #         for fv in final_field_values:
    #             cursor.execute(
    #                 """
    #                 INSERT INTO form_field_values (id, submission_id, field_id, value_text)
    #                 VALUES (%s, %s, %s, %s)
    #                 """,
    #                 (str(uuid.uuid4()), str(submission_id), fv["field_id"], fv["value"]),
    #             )

    #     return {
    #         "message": "Form submitted successfully",
    #         "submission_id": submission_id,
    #         "submitted_at": submitted_at,
    #     }
    async def submit_form_with_files(
    self,
    form_id: str,
    submitted_by: str,
    field_values: List[FieldValue],
    files: Optional[List[UploadFile]],
    s3: S3Service,
):
        """
        Save form submission and handle file uploads (one file per field if provided).
        """
        with get_db_connection(self.schema_id) as cursor:
            file_map = {}

            if files:
                # Upload all files concurrently
                upload_tasks = [s3.upload_file(file) for file in files]
                uploaded_urls = await asyncio.gather(*upload_tasks, return_exceptions=True)

                # Assign URLs to field_ids (match by order)
                for fv, url in zip(field_values, uploaded_urls):
                    if isinstance(url, Exception):
                        raise HTTPException(status_code=400, detail=f"File upload failed: {str(url)}")
                    file_map[str(fv.field_id)] = url

                logger.debug(f"File map: {file_map}")

            # Merge file URLs into field_values
            final_field_values = []
            for fv in field_values:
                fid = str(fv.field_id)
                if fid in file_map:
                    final_field_values.append({
                        "field_id": fid,
                        "value": file_map[fid]
                    })
                elif isinstance(fv.value, list):
                    final_field_values.append({
                        "field_id": fid,
                        "value": json.dumps(fv.value)
                    })
                else:
                    final_field_values.append({
                        "field_id": fid,
                        "value": str(fv.value) if fv.value is not None else None
                    })

            logger.debug(f"Final field values: {final_field_values}")

            submission_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO form_submissions (submission_id, form_id, submitted_by, submitted_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING submitted_at
                """,
                (submission_id, str(form_id), str(submitted_by)),
            )
            submitted_at = cursor.fetchone()[0]

            for fv in final_field_values:
                cursor.execute(
                    """
                    INSERT INTO form_field_values (id, submission_id, field_id, value_text)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (str(uuid.uuid4()), str(submission_id), fv["field_id"], fv["value"]),
                )

        return {
            "message": "Form submitted successfully",
            "submission_id": submission_id,
            "submitted_at": submitted_at,
        }

    
    
    async def update_form_with_files(
        self,
        submission_id: str,
        form_id: str,
        submitted_by: str,
        field_values: List[FieldValue],
        files: Optional[List[UploadFile]],
        s3: S3Service,
        parsed_data: Optional[FormUpdateRequest] = None,
    ):
        """
        Partially update form submission field values (and files if provided).
        Keeps old values if not overwritten.
        """
        with get_db_connection(self.schema_id) as cursor:
            # Ensure submission exists
            cursor.execute(
                "SELECT submission_id,flagged FROM form_submissions WHERE submission_id = %s AND form_id = %s AND flagged='approved'",
                (submission_id, form_id),
            )
            existing = cursor.fetchone()
            # print("this fatched data",existing)
            if not existing:
                raise HTTPException(status_code=403, detail="Form cannot be edited unless admin approves it")
             

            # Process files
            file_map = {}
            if files and parsed_data and parsed_data.file_mappings:
                upload_tasks = [s3.upload_file(files[mapping.file_index]) for mapping in parsed_data.file_mappings]
                uploaded_urls = await asyncio.gather(*upload_tasks, return_exceptions=True)

                for mapping, url in zip(parsed_data.file_mappings, uploaded_urls):
                    if isinstance(url, Exception):
                        raise HTTPException(status_code=400, detail=f"File upload failed: {str(url)}")
                    field_id = str(mapping.field_id)
                    if field_id not in file_map:
                        file_map[field_id] = []
                    file_map[field_id].append(url)

            # Build new values
            updates = {}
            for fv in field_values:
                fid = str(fv.field_id)
                if fid in file_map:
                    updates[fid] = json.dumps(file_map[fid])
                elif isinstance(fv.value, list):
                    updates[fid] = json.dumps(fv.value)
                else:
                    updates[fid] = str(fv.value) if fv.value is not None else None

            # Apply updates
            for field_id, new_value in updates.items():
                cursor.execute(
                    """
                    UPDATE form_field_values
                    SET value_text = %s
                    WHERE submission_id = %s AND field_id = %s
                    """,
                    (new_value, submission_id, field_id),
                )
                # If no row was updated (new field_id), insert it
                if cursor.rowcount == 0:
                    cursor.execute(
                        """
                        INSERT INTO form_field_values (id, submission_id, field_id, value_text)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (str(uuid.uuid4()), submission_id, field_id, new_value),
                    )

            # Update modified timestamp
            cursor.execute(
                "UPDATE form_submissions SET submitted_at = NOW() WHERE submission_id = %s",
                (submission_id,),
            )

        return {
            "message": "Form updated successfully",
            "submission_id": submission_id,
        }
    



    def get_form_by_submission_id(self, submission_id: str, user_id: str):
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(
                """
                SELECT fs.submission_id, fs.form_id, f.title AS form_title,
                    u.full_name AS submitted_by, fs.submitted_at, fs.flagged
                FROM form_submissions fs
                JOIN form f ON fs.form_id = f.form_id
                JOIN users u ON fs.submitted_by = u.user_id
                WHERE fs.submission_id = %s
                """,
                (submission_id,),
            )
            submission = cursor.fetchone()
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")

            (sub_id, form_id, form_title, submitted_by, submitted_at, flagged) = submission

            # fetch field values
            cursor.execute(
                """
                SELECT fsv.field_id, ff.name AS field_name, fsv.value_text ,ff.field_type
                FROM form_field_values fsv
                JOIN form_fields ff ON fsv.field_id = ff.field_id
                WHERE fsv.submission_id = %s
                """,
                (submission_id,),
            )
            field_rows = cursor.fetchall()

            field_values = []
            for field_id, field_name, value_text,field_type in field_rows:
                parsed_value = value_text
                try:
                    parsed_value = json.loads(value_text)  # if JSON stored
                except (json.JSONDecodeError, TypeError):
                    pass
                field_values.append({
                    "field_id": field_id,
                    "field_name": field_name,
                    "field_type": field_type,
                    "value": parsed_value
                })

            return {
                "submission_id": sub_id,
                "form_id": form_id,
                "form_title": form_title,
                "submitted_by": submitted_by,
                "submitted_at": submitted_at,
                "flagged": flagged,
                "field_values": field_values,
            }

    
# get all form submissions with filters and pagination
    async def get_all_submissions(
        self,
        form_id: Optional[str] = None,
        task_id: Optional[str] = None,
        submitted_by: Optional[str] = None,
        flagged: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 0,
        limit: int = 10,
        is_admin: bool = False
    ):
        offset = page * limit
        base_query = """
            SELECT fs.submission_id, fs.form_id, u.full_name AS submitted_by,
                   fs.submitted_at, fs.flagged, t.task_id,t.name, f.title
            FROM form_submissions fs
            JOIN users u ON fs.submitted_by = u.user_id
            JOIN form f ON fs.form_id = f.form_id
            JOIN task t ON f.task_id = t.task_id
            WHERE 1=1
        """
        params = []

        # Apply filters
        if form_id:
            base_query += " AND fs.form_id = %s"
            params.append(str(form_id))

        if task_id:
            base_query += " AND t.task_id = %s"
            params.append(str(task_id))

        if submitted_by:
            base_query += " AND fs.submitted_by = %s"
            params.append(str(submitted_by))
        flagged=flagged.lower() if flagged else None
        if flagged:
            if flagged not in ['raised', 'approved', 'rejected','none']:
                raise HTTPException(status_code=400, detail="Invalid flagged value. Must be 'raised', 'approved', or 'rejected'.")
            base_query += " AND fs.flagged = %s"
            params.append(flagged)

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%d-%m-%Y").date()
            base_query += " AND DATE(fs.submitted_at) >= %s"
            params.append(str(start_date_obj))

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%d-%m-%Y").date()
            base_query += " AND DATE(fs.submitted_at) <= %s"
            params.append(str(end_date_obj))

        # Count total for pagination
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as subquery"
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

        # Sorting + pagination (always latest first)
        final_query = base_query + " ORDER BY fs.submitted_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(final_query, tuple(params))
            rows = cursor.fetchall()

        submissions = []
        for row in rows:
            submission_id, form_id, submitted_by_name, submitted_at, flagged, task_id,task_name,form_title = row
            submissions.append({
                "submission_id": submission_id,
                "task_id": task_id,
                "task_name": task_name,
                "form_id": form_id,
                "form_title": form_title,
                "submitted_by": submitted_by_name,
                "submitted_at": submitted_at,
                "flagged": flagged
            })

        return submissions, total_count

    
    # get the form data based on user or all data related to form_id;
    async def get_my_form_submissions(
    self, form_id: Optional[str], user_id: str, page: int, limit: int):
        """
        Fetch form submissions by user.
        - If form_id provided -> submissions for that form.
        - Else -> group submissions by form_id (with form name).
        Supports pagination at form level (page starts at 0).
        """
        offset = page * limit

        with get_db_connection(self.schema_id) as cursor:
            if form_id:
                cursor.execute(
                    """
                    SELECT fs.submission_id, fs.form_id, f.title AS form_name,
                        fs.submitted_at, fsv.field_id, fsv.value_text
                    FROM form_submissions fs
                    JOIN form_field_values fsv ON fs.submission_id = fsv.submission_id
                    JOIN form f ON fs.form_id = f.form_id
                    WHERE fs.form_id = %s AND fs.submitted_by = %s
                    ORDER BY fs.submitted_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(form_id), str(user_id), limit, offset),
                )
                rows = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM form_submissions
                    WHERE form_id = %s AND submitted_by = %s
                    """,
                    (str(form_id), str(user_id)),
                )
                total_count = cursor.fetchone()[0]

            else:
                cursor.execute(
                    """
                    SELECT fs.submission_id, fs.form_id, f.title AS form_name,
                        fs.submitted_at, fsv.field_id, fsv.value_text
                    FROM form_submissions fs
                    JOIN form_field_values fsv ON fs.submission_id = fsv.submission_id
                    JOIN form f ON fs.form_id = f.form_id
                    WHERE fs.submitted_by = %s
                    ORDER BY fs.submitted_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(user_id), limit, offset),
                )
                rows = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM form_submissions
                    WHERE submitted_by = %s
                    """,
                    (str(user_id),),
                )
                total_count = cursor.fetchone()[0]

        if not rows:
            return [], total_count

        # Group submissions by form_id
        forms_map = {}
        for row in rows:
            submission_id, form_id, form_name, submitted_at, field_id, value_text = row

            if form_id not in forms_map:
                forms_map[form_id] = {
                    "form_id": form_id,
                    "form_name": form_name,
                    "submissions": []
                }

            # Check if submission already added
            submission = next((s for s in forms_map[form_id]["submissions"] if s["submission_id"] == submission_id), None)
            if not submission:
                submission = {
                    "submission_id": submission_id,
                    "submitted_at": submitted_at,
                    "field_values": []
                }
                forms_map[form_id]["submissions"].append(submission)

            # Decode JSON values if possible
            parsed_value = value_text
            try:
                parsed_value = json.loads(value_text)
            except (json.JSONDecodeError, TypeError):
                pass

            submission["field_values"].append({
                "field_id": field_id,
                "value": parsed_value
            })

        return list(forms_map.values()), total_count
    
    #get total form submissions of a user
    def get_total_form_submissions(self, user_id: str) -> int:
        with get_db_connection(self.schema_id) as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM form_submissions
                WHERE submitted_by = %s
                """,
                (str(user_id),),
            )
            
            total_count = cursor.fetchone()[0]
        return total_count           
    # get forms submitted by a specific user with optional form_id filter and pagination            
    async def get_submissions_by_user(
        self, user_id: str, form_id: Optional[str] = None, page: int = 0, limit: int = 10
    ):
        """
        Get forms submitted by a specific user.
        - If form_id is provided -> return detailed submissions with field names & values.
        - Else -> return all submissions (summary by submission).
        - Supports pagination.
        """
        offset = page * limit

        with get_db_connection(self.schema_id) as cursor:
            if form_id:
                # Step 1: Get paginated submissions (no field join here)
                cursor.execute(
                    """
                    SELECT fs.submission_id, fs.form_id, f.title AS form_name, fs.submitted_at
                    FROM form_submissions fs
                    JOIN form f ON fs.form_id = f.form_id
                    WHERE fs.submitted_by = %s AND fs.form_id = %s
                    ORDER BY fs.submitted_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(user_id), str(form_id), limit, offset),
                )
                submissions = cursor.fetchall()

                if not submissions:
                    return []

                submission_ids = [row[0] for row in submissions]
                submissions_map = {
                    row[0]: {
                        "submission_id": row[0],
                        "form_id": row[1],
                        "form_name": row[2],
                        "submitted_at": row[3],
                        "field_values": [],
                    }
                    for row in submissions
                }

                # Step 2: Fetch field values for those submissions
                cursor.execute(
                    """
                    SELECT fsv.submission_id, fsv.field_id, ff.name AS field_name, fsv.value_text
                    FROM form_field_values fsv
                    JOIN form_fields ff ON fsv.field_id = ff.field_id
                    WHERE fsv.submission_id = ANY(%s::uuid[])
                    ORDER BY fsv.submission_id
                    """,
                    (submission_ids,),
                )
                field_rows = cursor.fetchall()

                for submission_id, field_id, field_name, value_text in field_rows:
                    parsed_value = value_text
                    try:
                        parsed_value = json.loads(value_text)
                    except (json.JSONDecodeError, TypeError):
                        pass

                    submissions_map[submission_id]["field_values"].append(
                        {
                            "field_id": field_id,
                            "field_name": field_name,
                            "value": parsed_value,
                        }
                    )

                return list(submissions_map.values())

            else:
                # Summary of all submissions (paginated)
                cursor.execute(
                    """
                    SELECT fs.submission_id, f.form_id, f.title AS form_name, fs.submitted_at
                    FROM form_submissions fs
                    JOIN form f ON fs.form_id = f.form_id
                    WHERE fs.submitted_by = %s
                    ORDER BY fs.submitted_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(user_id), limit, offset),
                )
                rows = cursor.fetchall()

                if not rows:
                    return []

                return [
                    {
                        "submission_id": row[0],
                        "form_id": row[1],
                        "form_name": row[2],
                        "submitted_at": row[3],
                    }
                    for row in rows
                ]
                
    async def count_submissions_by_user(self, user_id: str, form_id: Optional[str] = None) -> int:
        """
        Count total submissions by a specific user.
        - If form_id is provided -> count submissions for that form only.
        - Else -> count all submissions by the user.
        """
        with get_db_connection(self.schema_id) as cursor:
            if form_id:
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM form_submissions 
                    WHERE submitted_by = %s AND form_id = %s
                    """,
                    (str(user_id), str(form_id)),
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM form_submissions 
                    WHERE submitted_by = %s
                    """,
                    (str(user_id),),
                )

            result = cursor.fetchone()
            return result[0] if result else 0
                
                
    # Flag a submission (raise, approve, reject) with notifications
        
    async def flag_submission(
            self,
            submission_id: str,
            flagged_by: str,
            flag_status: str,
            is_admin: bool
        ):
            """
            Flag a form submission (raised, approved, rejected).
            Sends notifications based on flag action.
            """

            with get_db_connection(self.schema_id) as cursor:
                #  Ensure submission exists
                cursor.execute(
                    "SELECT form_id, submitted_by FROM form_submissions WHERE submission_id = %s",
                    (submission_id,),
                )
                existing = cursor.fetchone()
                # print("this fatched data",existing)
                if not existing:
                    raise HTTPException(status_code=404, detail="Submission not found")

                form_id, submission_owner = existing

                #  Get flagging user's name
                cursor.execute(
                    "SELECT full_name FROM users WHERE user_id = %s", (flagged_by,)
                )
                user_record = cursor.fetchone()
                flagger_name = user_record[0] if user_record else "User"

                #  Get form name
                cursor.execute("SELECT title,created_by FROM form WHERE form_id = %s", (form_id,))
                form_record = cursor.fetchone()
                # print("thus form id",form_id)
                # print("this fatched data",form_record)
                form_name = form_record[0] if form_record else "Form"
                form_created_by = form_record[1] if form_record else None

                #  Only admins can approve/reject
                if not is_admin and flag_status in ["approved", "rejected"]:
                    raise HTTPException(status_code=403, detail="Only admins can approve or reject flags")

                #  Update flag status
                cursor.execute(
                    "UPDATE form_submissions SET flagged = %s WHERE submission_id = %s",
                    (flag_status, submission_id),
                )

                # ==============================
                # Notifications
                # ==============================
                if flag_status == "raised":
                    # Notify admins
                    cursor.execute(
                        """
                        INSERT INTO notifications (user_id,form_id, title, message, created_at, created_by,submission_id)
                        VALUES (%s,%s, 'Flag Raised', %s, %s, %s, %s)
                        """,
                        (   form_created_by,   # or admin_id (loop over admins if needed)
                             form_id,
                            f"'{flagger_name}' raised a flag on '{form_name}' form.",
                            datetime.now(),
                            flagged_by,
                            submission_id
                        ),
                    )

                elif flag_status in ["approved", "rejected"]:
                    # Notify submission owner
                    cursor.execute(
                        """
                        INSERT INTO notifications (user_id,form_id, title, message, created_at, created_by,submission_id)
                        VALUES (%s, %s,'Flag {status}', %s, %s, %s, %s)
                        """.format(status=flag_status.capitalize()),
                        (
                            submission_owner,
                            form_id,
                            f"Your submission for '{form_name}' was {flag_status} by {flagger_name}",
                            datetime.now(),
                            flagged_by,
                            submission_id
                        ),
                    )

            return {
                "message": f"{flag_status} request to edit form successfully"
                # "submission_id": submission_id,
                # "flagged_by": flagged_by,
                # "notifications_created": notifications_created,
            }