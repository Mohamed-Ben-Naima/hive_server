# Hive-server/main.py

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
import os

# Load environment variables at the very top of the main entry file
load_dotenv()

# Import all app setup utilities and settings from app_setup.
from .utils.app_setup import (
    app_lifespan,
    setup_app_middleware,
    setup_exception_handlers,
    APP_NAME,
    APP_VERSION,
    DEBUG_MODE,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    CORS_ORIGINS,
    CORS_METHODS,
    CORS_HEADERS
)
from .utils.db import get_db

# Import all API routers.
from .routers import auth as auth_router
from .routers import users as users_router
from .routers import posts as posts_router
from .routers import post_likes as post_likes_router
from .routers import post_comments as post_comments_router # <--- NEW: Import the post_comments router

from .schemas import user as user_schema # For test_error_endpoint

# Initialize FastAPI application.
app = FastAPI(
    title=APP_NAME,
    description="API for Tea & Hive mobile application.",
    version=APP_VERSION,
    lifespan=app_lifespan
)

# --- Apply Middlewares ---
setup_app_middleware(app)

# --- Register Global Exception Handlers ---
setup_exception_handlers(app)

# --- Include Routers ---
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(posts_router.router)
app.include_router(post_likes_router.router)
app.include_router(post_comments_router.router) # <--- NEW: Include the post_comments router

# --- Serve Static Files (Uploads) ---
upload_dir_path = os.getenv("UPLOAD_DIRECTORY_PATH", "uploads")
app.mount("/uploads", StaticFiles(directory=upload_dir_path), name="uploads")
print(f"Mounted static files from '{upload_dir_path}' at '/uploads/'")

# --- Root Endpoint ---
@app.get("/", summary="Root endpoint", description="Returns a welcome message.")
def read_root():
    return {"message": "Welcome to Tea & Hive Backend 🍯!"}

# --- Test Database Endpoint (for quick verification) ---
@app.get("/test-db-endpoint/", summary="Test database connection", description="Verifies the database connection by requesting a session.")
def test_db_endpoint(db: Session = Depends(get_db)):
    return {"message": "This endpoint successfully accessed the database session."}

# --- Test Exception Endpoint (for quick verification of handlers) ---
@app.get("/test-error/{error_type}", summary="Test exception handler", description="Triggers different types of errors to test the global exception handler.")
def test_error_endpoint(error_type: str):
    from fastapi import HTTPException, status
    from fastapi.exceptions import RequestValidationError
    from pydantic import ValidationError

    if error_type == "http":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This is a test HTTP error (Bad Request).")
    elif error_type == "generic":
        result = 1 / 0
        return {"result": result}
    elif error_type == "validation":
        try:
            user_schema.UserCreate(email="invalid", password="1", verify_password="1")
        except ValidationError as e:
            raise RequestValidationError(e.errors())
    else:
        return {"message": "Specify 'http', 'generic', or 'validation' to test errors."}
