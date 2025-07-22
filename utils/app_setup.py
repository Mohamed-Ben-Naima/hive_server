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
import logging
import sys

# Load environment variables here as well, to ensure they are available
load_dotenv()

# --- Configure Logger ---
logger = logging.getLogger("tea_n_hive_logger")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(console_handler)
if os.getenv("DEBUG_MODE", "False").lower() == "true":
    logger.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)
    logger.debug("DEBUG_MODE is ON. Logging level set to DEBUG.")


# --- Application Settings (Centralized here) ---
APP_NAME = "Tea & Hive Backend"
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-that-is-at-least-32-chars-long")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 5))

CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(',') if origin.strip()] if CORS_ORIGINS_STR != "*" else ["*"]
CORS_METHODS = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(',')
CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(',')

# Import database utilities (relative to utils package)
from .db import test_db_connection, engine
from ..models.base import Base
# --- CRITICAL: Import all your SQLAlchemy model files here to ensure they are loaded ---
from ..models import user
from ..models import posts
from ..models import post_likes
from ..models import post_comments # <--- NEW: Import the post_comments model file
# --- END CRITICAL IMPORTS ---

# --- Lifespan Context Manager ---
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    Performs database connection test and SQLAlchemy mapper configuration.
    """
    logger.info(f"🚀 Starting {APP_NAME} v{APP_VERSION} 🚀")
    logger.info("Attempting database connection test on server startup...")

    if test_db_connection():
        logger.info("✅ Database connection successful on startup! ✅")
        # --- CRITICAL STEP: CONFIGURE SQLAlchemy MAPPERS ---
        # This call resolves all string-based relationship definitions (e.g., "User", "Post")
        # after all models have been imported and registered with the declarative base.
        Base.registry.configure()
        logger.info("✅ SQLAlchemy mappers configured successfully.")
        # --- END CRITICAL STEP ---

        # Optional: Database Table Creation (for development only)
        # if DEBUG_MODE:
        #     logger.info("Attempting to create database tables (development mode)...")
        #     Base.metadata.create_all(bind=engine)
        #     logger.info("Database tables ensured (development mode).")
    else:
        logger.critical("❌ Database connection FAILED on startup. Exiting application. ❌")
        sys.exit(1)

    yield

    logger.info("Shutting down FastAPI application.")

# --- Middleware Setup Function ---
def setup_app_middleware(app: FastAPI):
    """Configures application-wide middlewares."""
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
    """Registers global exception handlers for consistent error responses."""

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
        logger.exception(f"Unhandled Exception caught for URL: {request.url}. Error: {exc}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An unexpected server error occurred."},
        )
    logger.info("Global exception handlers registered.")
