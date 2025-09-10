import os
from dotenv import load_dotenv
from jose import jwt  # using python-jose
from jose.exceptions import JWTError  # correct exception class

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from app.configuration.database import get_db_connection

load_dotenv()


def setup_middlewares(app: FastAPI):
    # Middleware 1: Auth
    @app.middleware("http")
    async def AuthMiddleware(request: Request, call_next):
        if request.url.path.startswith("/auth"):
            # If the path is not a protected JWT route, skip this middleware.
            print("Running AuthMiddleware and skiping kk  for path:", request.url.path)

            return await call_next(request)
        
                    
        else:
            print("Running AuthMiddleware for path:", request.url.path)

            auth_header = request.headers.get("Authorization")
            print("AUTH HEADER:", auth_header)

            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authorization header missing or invalid"}
                )

            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
                print("PAYLOAD:", payload)
                request.state.user = payload
            except JWTError as e:
                return JSONResponse(status_code=401, content={"detail": f"Invalid token: {e}"})

            response = await call_next(request)
            return response

    # Middleware 2: Schema Switcher
    @app.middleware("http")
    async def SchemaSwitcherMiddleware(request: Request, call_next):
        if not request.url.path.startswith("/external"):
            return await call_next(request)

        if not hasattr(request.state, 'user'):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed, cannot determine schema."},
            )

        schema = request.state.user.get("schema_id")
        if not schema:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token is valid, but 'schema_id' is missing."},
            )

        try:
            with get_db_connection(schema) as db_cursor:
                request.state.db_cursor = db_cursor
                response = await call_next(request)
            return response
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Database error for schema '{schema}': {e}"},
            )

                
