# Hive-server/main.py

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
import os
import logging
from pathlib import Path # <--- NEW: Import Path

# Define the path to the .env file explicitly
# Assumes .env is in the same directory as main.py (i.e., hive_server/)
# and you are running uvicorn from the parent directory (Hive-app/)
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path) # <--- IMPORTANT: Pass the explicit path

# Import all app setup utilities and settings.
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
    CORS_HEADERS,
    DATABASE_URL # Import the constructed DATABASE_URL
)
# Import db utilities and the new initialization function
from .utils.db import get_db, initialize_db_engine, get_engine

logger = logging.getLogger("tea_n_hive_logger")

# --- Initialize FastAPI application. ---
app = FastAPI(
    title=APP_NAME,
    description="API for Tea & Hive mobile application.",
    version=APP_VERSION,
    lifespan=app_lifespan
)

# --- IMPORTANT: Initialize the database engine here, before app startup ---
try:
    initialize_db_engine(DATABASE_URL)
except ValueError as e:
    logger.critical(f"Failed to initialize database engine: {e}. Exiting.")
    import sys
    sys.exit(1)


# --- Apply Middlewares ---
setup_app_middleware(app)

# --- Register Global Exception Handlers ---
setup_exception_handlers(app)

# --- Include Routers ---
from .routers import auth as auth_router
from .routers import users as users_router
from .routers import posts as posts_router
from .routers import post_likes as post_likes_router
from .routers import post_comments as post_comments_router
from .routers import shorts as shorts_router
from .routers import short_likes as short_likes_router
from .routers import short_comments as short_comments_router

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(posts_router.router)
app.include_router(post_likes_router.router)
app.include_router(post_comments_router.router)
app.include_router(shorts_router.router)
app.include_router(short_likes_router.router)
app.include_router(short_comments_router.router)

# --- Serve Static Files (Uploads) ---
upload_dir_path = os.getenv("UPLOAD_DIRECTORY_PATH", "uploads")
os.makedirs(upload_dir_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir_path), name="uploads")
logger.info(f"Mounted static files from '{upload_dir_path}' at '/uploads/'")

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
    from .schemas import user as user_schema # Local import for schema

    if error_type == "http":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This is a test HTTP error (Bad Request).")
    elif error_type == "generic":
        result = 1 / 0
        return {"result": result}
    elif error_type == "validation":
        try:
            class DummySchema(user_schema.BaseModel):
                email: str
                password: str
            DummySchema(email="invalid", password="1")
        except ValidationError as e:
            raise RequestValidationError(e.errors())
    else:
        return {"message": "Specify 'http', 'generic', or 'validation' to test errors."}
