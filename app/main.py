from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import auth_middleware
from app.routes.admim_routes.user_router import user_router as user_router
from app.routes.admim_routes.user_router import admin_router as admin_router
from app.routes.task_router import task_router as task_router
from app.routes.form_router import form_router as form_router
from app.routes.form_submissions_routes import (
    form_submissions_router as form_submissions_router,flag_submission_router as flag_submission_router,filter_router as filter_router
)


from app.routes.AccessToForm_routes import AccessToForm_routes as accessToForm_routes
from app.routes.notification_router import notification_router as notification_router
from app.routes.external_router import external_router
from app.configuration.database import initialize_db_pool, db_pool
# from app.routes.report_router import router as report_router

# from app.routes.user_router import router as user_router

app = FastAPI()

# Set up middlewares (custom auth middleware, etc.)
auth_middleware.setup_middlewares(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root route
@app.get("/")
async def root():
    return {"message": "Welcome to the RishiKrishi API"}


# Startup and shutdown events
@app.on_event("startup")
def on_startup():
    """Initialize resources on startup."""
    initialize_db_pool()


@app.on_event("shutdown")
def on_shutdown():
    """Clean up resources on shutdown."""
    if db_pool:
        db_pool.closeall()
        print("Database connection pool closed.")


# Main router setup
main_router = APIRouter(prefix="/api", tags=["main"])
main_router.include_router(external_router)
# main_router.include_router(user_router)
app.include_router(main_router)
app.include_router(admin_router)
app.include_router(user_router)
app.include_router(task_router)
app.include_router(form_router)
app.include_router(form_submissions_router)
app.include_router(flag_submission_router)
app.include_router(accessToForm_routes)
app.include_router(notification_router)

app.include_router(filter_router)

# Reports
# app.include_router(report_router)


# Run the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
