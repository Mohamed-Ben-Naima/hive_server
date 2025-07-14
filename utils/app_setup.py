# Hive-server/utils/app_setup.py

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session # For type hinting in lifespan
from sqlalchemy import text # For database connection test
import traceback # For logging unhandled exceptions
import os # For environment variables
from dotenv import load_dotenv # For loading .env

# Load environment variables here as well, to ensure they are available
# when this module is imported, especially if other modules depend on them early.
load_dotenv()

# --- Application Settings (moved here from main.py) ---
APP_NAME = "Tea & Hive Backend"
APP_VERSION = "0.1.0"
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "default-super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS settings (moved here from main.py)
CORS_ORIGINS = ["*"] # IMPORTANT: Restrict this in production (e.g., ["http://localhost:3000", "https://yourdomain.com"])
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS = ["*"]

# Import database utilities (relative to utils package)
from .db import test_db_connection, engine # 'engine' is needed if Base.metadata.create_all is used
from ..models.base import Base # Import Base for optional table creation

# --- Lifespan Context Manager ---
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    Handles database connection testing and optional table creation.
    """
    print(f"\n🚀 Starting {APP_NAME} v{APP_VERSION} 🚀")
    print("Attempting database connection test on server startup...")

    if test_db_connection():
        print("✅ Database connection successful on startup! ✅")
        # --- Optional: Database Table Creation (for development only) ---
        # In a production environment, you would use a migration tool like Alembic
        # to manage your database schema changes. Uncomment the following lines
        # ONLY for initial development setup if you want FastAPI to create tables.
        # Base.metadata.create_all(bind=engine)
        # print("Database tables ensured (development mode).")
    else:
        print("❌ Database connection FAILED on startup. Exiting application. ❌")
        # If the database connection is critical, exit the application.
        import sys
        sys.exit(1)

    yield # The application starts here

    # Shutdown event logic
    print("\nShutting down FastAPI application.")

# --- Middleware Setup Function ---
def setup_app_middleware(app: FastAPI):
    """
    Configures and adds CORS (Cross-Origin Resource Sharing) middleware to the FastAPI application.
    """
    from starlette.middleware.cors import CORSMiddleware # Imported locally to keep this file cleaner
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=CORS_METHODS,
        allow_headers=CORS_HEADERS,
    )

# --- Global Exception Handlers Setup Function ---
def setup_exception_handlers(app: FastAPI):
    """
    Registers global exception handlers for the FastAPI application.
    """
    # Handler for Pydantic's RequestValidationError (for invalid request bodies/queries/paths)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        print(f"Request Validation Error caught for URL: {request.url}")
        print(f"Validation errors: {exc.errors()}")

        error_messages = []
        for error in exc.errors():
            field = ".".join(map(str, error["loc"]))
            message = error["msg"]
            error_messages.append(f"Field '{field}': {message}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": "Validation error", "details": error_messages},
        )

    # Handler for FastAPI's HTTPException (e.g., 404 Not Found, 400 Bad Request)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        print(f"HTTP Exception caught: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )

    # Handler for any other unexpected exceptions (generic server errors)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        print(f"Unhandled Exception caught: {exc}")
        traceback.print_exc() # Prints the full traceback to the console/logs

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An unexpected server error occurred."},
        )