# from psycopg2 import pool
# import os

# from dotenv import load_dotenv
# load_dotenv()
# # PostgreSQL DB config
# DB_CONFIG = {
#     "host": os.getenv("DB_HOST"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "dbname": os.getenv("DATABASE_NAME"), # 🔁 use dbname for PostgreSQL
#     "port": os.getenv("DATABASE_PORT")  # correct port for PostgreSQL
# }

# # Create a connection pool
# db_pool = pool.SimpleConnectionPool(
#     minconn=1,
#     maxconn=5,
#     **DB_CONFIG
# )
# def get_db_pool():
#     """
#     Dependency to get a database connection pool.
#     """
#     return db_pool


from psycopg2 import pool
import os
from dotenv import load_dotenv

load_dotenv()


# Create the pool


import os
import jwt  # PyJWT library for token handling
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from fastapi import FastAPI, Request, HTTPException, APIRouter
from pydantic import BaseModel, Field
from typing import Optional

# --- Configuration (Simulating .env) ---
# In a real app, use a library like python-dotenv to load these

# --- 1. Database Pool and Connection Management ---
# This section sets up the connection pool and the crucial context manager.

db_pool = None


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DATABASE_NAME"),
    "port": int(os.getenv("DATABASE_PORT", "5432")),
}


def initialize_db_pool():
    """Initializes the connection pool. Call this once at application startup."""
    global db_pool
    if db_pool is None:
        try:
            print("Initializing database connection pool...")
            db_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=DB_CONFIG["dbname"],
                port=DB_CONFIG["port"],
            )
            print("Database pool initialized successfully.")
        except psycopg2.OperationalError as e:
            print(f"FATAL: Could not connect to database: {e}")
            # In a real app, you might exit or have a retry mechanism
            raise RuntimeError(f"Error creating DB pool: {e}")


# @contextmanager
# def get_db_connection(schema: str):
#     """
#     A context manager to handle the database connection lifecycle.
#     - Gets a connection from the pool.
#     - Sets the session's search_path to the provided schema.
#     - Yields a cursor for database operations.
#     - Commits on success, rolls back on error.
#     - Always returns the connection to the pool.
#     """
#     if not schema:
#         raise ValueError("Schema name must be provided.")
#     if not db_pool:
#         raise RuntimeError("Database pool is not initialized.")

#     conn = None
#     try:
#         conn = db_pool.getconn()
#         with conn.cursor() as cur:
#             # IMPORTANT: Set the search_path for the current transaction.
#             # This is session-specific and won't affect other requests.
#             # Using a placeholder prevents SQL injection on the schema name.
#             cur.execute("SET search_path TO %s;", (schema,))
#             print(f"DB Context: search_path set to '{schema}' for this request.")
#             yield cur
#         conn.commit() # Commit the transaction if everything was successful
#     except Exception as e:
#         if conn:
#             conn.rollback() # Rollback on any error
#         print(f"Error in DB context for schema '{schema}': {e}")
#         # Re-raise the exception to be handled by FastAPI's error handling
#         raise
#     finally:
#         if conn:
#             db_pool.putconn(conn)
#             print(f"DB Context: Connection returned to pool for schema '{schema}'.")


@contextmanager
def get_db_connection(schema: str):
    if not schema:
        raise ValueError("Schema name must be provided.")
    if not db_pool:
        raise RuntimeError("Database pool is not initialized.")

    conn = None
    cur = None
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        # set schema
        cur.execute(f"SET search_path TO {schema};")
        yield cur
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in DB context for schema '{schema}': {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            db_pool.putconn(conn)
            print(f"DB Context: Connection returned to pool for schema '{schema}'.")
