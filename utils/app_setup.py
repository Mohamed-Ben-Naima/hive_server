# Hive-server/utils/app_setup.py

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import text
import traceback
import os
from dotenv import load_dotenv
import logging # <-- NEW: Import logging

# Load environment variables here as well, to ensure they are available
load_dotenv()

# --- Configure Logger ---
# Create a logger instance
logger = logging.getLogger("tea_n_hive_logger") # Give your logger a name
logger.setLevel(logging.INFO) # Set the default logging level

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # Set handler level

# Create a formatter (e.g., including timestamp, log level, logger name, and message)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)

# Add the handler to the logger
if not logger.handlers: # Prevent adding multiple handlers if reloaded
    logger.addHandler(console_handler)

# If DEBUG_MODE is true, set logger to DEBUG level
if os.getenv("DEBUG_MODE", "False").lower() == "true":
    logger.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG) # Ensure handler also logs debug messages
    logger.debug("DEBUG_MODE is ON. Logging level set to DEBUG.")


# --- Application Settings (Centralized here) ---
APP_NAME = "Tea & Hive Backend" # Corrected App Name
APP_VERSION = os.getenv("APP_VERSION", "0.6.0")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-that-is-at-least-32-chars-long")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(',') if origin.strip()] if CORS_ORIGINS_STR != "*" else ["*"]
CORS_METHODS = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(',')
CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(',')

# Import database utilities (relative to utils package)
from .db import test_db_connection, engine
from ..models.base import Base

# --- Lifespan Context Manager ---
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {APP_NAME} v{APP_VERSION} 🚀")
    logger.info("Attempting database connection test on server startup...")

    if test_db_connection():
        logger.info("✅ Database connection successful on startup! ✅")
        # Optional: Database Table Creation (for development only)
        # if DEBUG_MODE: # Only create tables in debug mode for safety
        #     Base.metadata.create_all(bind=engine)
        #     logger.info("Database tables ensured (development mode).")
    else:
        logger.critical("❌ Database connection FAILED on startup. Exiting application. ❌")
        import sys
        sys.exit(1)

    yield

    logger.info("Shutting down FastAPI application.")

# --- Middleware Setup Function ---
def setup_app_middleware(app: FastAPI):
    from starlette.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=CORS_METHODS,
        allow_headers=CORS_HEADERS,
    )
    logger.info("CORS middleware configured.")


# --- Global Exception Handlers Setup Function ---
def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Request Validation Error for URL: {request.url}. Details: {exc.errors()}")

        error_messages = []
        for error in exc.errors():
            field = ".".join(map(str, error["loc"]))
            message = error["msg"]
            error_messages.append(f"Field '{field}': {message}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": "Validation error", "details": error_messages},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP Exception caught: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Log the full traceback for unhandled exceptions
        logger.exception(f"Unhandled Exception caught for URL: {request.url}. Error: {exc}") # logger.exception logs traceback automatically

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An unexpected server error occurred."},
        )
    logger.info("Global exception handlers registered.")