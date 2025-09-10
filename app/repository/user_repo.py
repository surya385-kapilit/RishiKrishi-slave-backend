
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.configuration.database import get_db_connection

def user_exists_by_email(email: str,db_cursor) -> bool:
    # Placeholder for actual implementation to check if user exists by email
    db_cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    result = db_cursor.fetchone()
    if result:
        return True
    return False  
# Assume no user exists for simplicity

def user_exists_by_phone(phone: str,db_cursor) -> bool:

    db_cursor.execute("SELECT 1 FROM users WHERE phone = %s", (phone,))
    result = db_cursor.fetchone()
    if result:
        return True
    # Placeholder for actual implementation to check if user exists by phone

    return False

def create_user(email: str, name: str, role: str, phone: str, db_cursor) -> tuple[str, bool]:

    # try to create user in db and get user id from that
    db_cursor.execute("""
        INSERT INTO users (email, full_name, role, phone)
        VALUES (%s, %s, %s, %s) RETURNING user_id
    """, (email, name, role, phone))
    user_id = db_cursor.fetchone()[0]
    if user_id:
        return user_id, True
    else:
        return "", False
    

#get Users list
def get_users_list(db_cursor) -> list[dict]:
    query = """
        SELECT user_id, email, full_name, role, phone, status
        FROM users where role!='ADMIN'
    """
    db_cursor.execute(query)
    users = db_cursor.fetchall()

    # Return full details for all users
    return [
        {
            "user_id": user[0],
            # "email": user[1],
            "name": user[2],
            # "role": user[3],
            # "phone": user[4],
            # "status": user[5]
        } for user in users
    ]

# Get all users except current user with pagination
def get_all_users(db_cursor, user_type: str, current_user_id: str, page: int, limit: int) -> tuple[list[dict], int]:
    base_query = """
        SELECT user_id, email, full_name, role, phone, status
        FROM users
        WHERE user_id != %s
    """
    params = [current_user_id]

    if user_type.lower() == "admins":
        base_query += " AND role = 'ADMIN'"
    elif user_type == "supervisors":
        base_query += " AND role = 'SUPERVISOR'"

    # Count total
    count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subquery"
    db_cursor.execute(count_query, params)
    total_users = db_cursor.fetchone()[0]

    # Apply pagination
    offset = page * limit
    paginated_query = base_query + " ORDER BY full_name ASC LIMIT %s OFFSET %s"
    db_cursor.execute(paginated_query, params + [limit, offset])
    users = db_cursor.fetchall()

    if user_type in ["admins", "supervisors"]:
        return (
            [
                {
                    "user_id": user[0],
                    "email": user[1],
                    "name": user[2],
                    "role": user[3],
                    "phone": user[4],
                    "status": user[5]
                } for user in users
            ],
            total_users
        )
    else:
        return (
            [
                {
                    "user_id": user[0],
                    "email": user[1],
                    "name": user[2],
                    "role": user[3],
                    "phone": user[4],
                    "status": user[5]
                } for user in users
            ],
            total_users
        )
    
def get_user_by_id(user_id: str, db_cursor) -> dict | None:
    db_cursor.execute("""
        SELECT user_id, email, full_name, role, phone, status
        FROM users
        WHERE user_id = %s
    """, (user_id,))
    user = db_cursor.fetchone()
    if user:
        return {
            "user_id": user[0],
            "email": user[1],
            "name": user[2],
            "role": user[3],
            "phone": user[4],
            "status": user[5]
        }
    return None


def get_admin_name_by_id(schema_id:str):
    try:
        with get_db_connection(schema_id) as db_cursor:
            db_cursor.execute("""
                SELECT full_name
                FROM users
                WHERE role = 'ADMIN'
                LIMIT 1
            """)
            admin = db_cursor.fetchone()
            if admin:
                return admin[0]
            else:
                return "Admin"
    except Exception as e:
        print("Database access failed:", e)
        return "Admin"
    
def get_user_by_id_service(user_id: str, schema_id: str, admin_name: str):
    try:
        with get_db_connection(schema_id) as db_cursor:
            db_cursor.execute("""
                SELECT user_id, email, full_name, role, phone, status
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            user = db_cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found in tenant")
            
            return {
                "user_id": user[0],
                "email": user[1],
                "name": user[2],
                "role": user[3],
                "phone": user[4],
                "status": user[5],
                "admin_name": admin_name
            }
    except HTTPException:
        raise
    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving user")
    
#Get Admin dashboard details
def get_admin_dashboard_details(schema_id: str) -> dict:
    try:
        with get_db_connection(schema_id) as db_cursor:
            # Total users
            db_cursor.execute("SELECT COUNT(*) FROM users")
            total_users = db_cursor.fetchone()[0]

            # Active users
            db_cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            active_users = db_cursor.fetchone()[0]

            # Inactive users
            # db_cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'INACTIVE'")
            # inactive_users = db_cursor.fetchone()[0]
            
            #Total Tasks
            
            db_cursor.execute("SELECT COUNT(*) FROM task")
            total_tasks = db_cursor.fetchone()[0]
                
            # Total forms
            db_cursor.execute("SELECT COUNT(*) FROM form")
            total_forms = db_cursor.fetchone()[0]

            # Total submissions
            db_cursor.execute("SELECT COUNT(*) FROM form_submissions")
            total_submissions = db_cursor.fetchone()[0]

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_tasks": total_tasks,
                "total_forms": total_forms,
                "total_submissions": total_submissions
            }
    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving dashboard details")


# Get User dashboard details
def get_user_dashboard_details(schema_id: str, user_id: str) -> dict:
    try:
        with get_db_connection(schema_id) as db_cursor:
            # Total submissions by user
            db_cursor.execute(
                "SELECT COUNT(*) FROM form_submissions WHERE submitted_by = %s",
                (user_id,)
            )
            total_submissions = db_cursor.fetchone()[0]

            # Flagged submissions by user
            db_cursor.execute(
                "SELECT COUNT(*) FROM form_submissions WHERE submitted_by = %s AND flagged = 'raised'",
                (user_id,)
            )
            flagged_submissions = db_cursor.fetchone()[0]

            # Approved submissions by user
            db_cursor.execute(
                "SELECT COUNT(*) FROM form_submissions WHERE submitted_by = %s AND flagged = 'approved'",
                (user_id,)
            )
            approved_submissions = db_cursor.fetchone()[0]

            #Rejected submissions by user
            db_cursor.execute(
                "SELECT COUNT(*) FROM form_submissions WHERE submitted_by = %s AND flagged = 'rejected'",
                (user_id,)
            )
            rejected_submissions = db_cursor.fetchone()[0]

            return {
                "total_submissions": total_submissions,
                "raised_submissions": flagged_submissions,
                "approved_submissions": approved_submissions,
                "rejected_submissions": rejected_submissions
            }

    except Exception as e:
        print("Database access failed:", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving user dashboard details"
        )
