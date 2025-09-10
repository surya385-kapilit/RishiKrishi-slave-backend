import requests
from app.repository import user_repo
import requests
from fastapi import HTTPException
import os

from fastapi import HTTPException
from app.configuration.database import get_db_connection

SENTRY_URL = os.getenv("SENTRY_URL")  # fallback to localhost
def create_user_in_sentry(user_data: dict, token: str):
    url = f"{SENTRY_URL}/api/external/create-user"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print(f"Sending to Sentry: URL={url}, Headers={headers}, Data={user_data}")
    response = requests.post(url, json=user_data, headers=headers)
    print(f"Response from Sentry: {response.status_code}, {response.text}")

    if response.status_code != 201:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create user in sentry: {response.json().get('detail')}",
        )
    return response.json()


def update_user_in_sentry(user_id: str, user_data: dict, token: str):
    url = f"{SENTRY_URL}/api/external/update-user/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.put(url, json=user_data, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to update user in sentry: {response.json().get('detail')}"
        )   
    return response.json()

def delete_user_in_sentry(user_id: str, token: str):
    url = f"{SENTRY_URL}/api/external/delete-user/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to delete user in sentry: {response.json().get('detail')}"
        )   
    return response.json()

def userAlreadyExists(username: str, db_cursor) -> bool:
    with_email = False
    if "@" in username:
        with_email = True
    if with_email:
        return user_repo.user_exists_by_email(username, db_cursor)
    else:
        return user_repo.user_exists_by_phone(username, db_cursor)
    return False

def create_user(email: str, name: str, role: str, phone: str, db_cursor) -> tuple[str, bool]:
    return user_repo.create_user(email, name, role, phone, db_cursor)



def userAlreadyExists(username: str,db_cursor) -> bool:
    with_email = False
    if "@" in username:
        with_email = True
    if with_email:
        # Check if user exists by email
        return user_repo.user_exists_by_email(username, db_cursor)
    else:
        # Check if user exists by username
        return user_repo.user_exists_by_phone(username, db_cursor)
    # This is a placeholder for the actual implementation that checks if a user already exists
    return False  # Assume no user exists for simplicity

def create_user(email: str, name: str, role: str, phone: str,db_cursor) -> tuple[str, bool]:
    return user_repo.create_user(email, name, role, phone, db_cursor)
    


