from fastapi import APIRouter, Request


from app.middleware.auth_middleware import JWTAuthMiddleware

auth_router = APIRouter(prefix="/auth", tags=["auth"])
@auth_router.post("/login")
def login(request: Request):
    user_name=request.json().get("username")
    password=request.json().get("password")

    if '@' in user_name:
        # Assuming this is an email
       successfully= loginwith_email(user_name, password)
    else:
        # Assuming this is a username
       successfully= loginwith_phonenumber(user_name, password)
    if not successfully:
        return {"detail": "Invalid credentials"}, 401
    return {"detail": "Login successful"}, 200
    