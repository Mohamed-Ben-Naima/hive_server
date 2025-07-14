# Hive-server/main.py

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session # For type hinting in test_db_endpoint
from dotenv import load_dotenv # <-- Keep load_dotenv here for initial env loading

# Load environment variables at the very top of the main entry file
load_dotenv()

# Import app setup utilities from utils
from .utils.app_setup import app_lifespan, setup_app_middleware, setup_exception_handlers, APP_NAME, APP_VERSION # <-- NEW IMPORTS
from .utils.db import get_db # Database session dependency
from .routers import auth as auth_router # Authentication router
from .schemas import user as user_schema # For test_error_endpoint if it remains

# Initialize FastAPI application
app = FastAPI(
    title=APP_NAME,
    description="API for Tea & Hive mobile application.",
    version=APP_VERSION,
    lifespan=app_lifespan # Register the lifespan context manager
)

# --- Apply Middlewares ---
setup_app_middleware(app) # Call the middleware setup function

# --- Register Global Exception Handlers ---
setup_exception_handlers(app) # Call the exception handlers setup function

# --- Include Routers ---
app.include_router(auth_router.router)

# --- Root Endpoint ---
@app.get("/", summary="Root endpoint", description="Returns a welcome message.")
def read_root():
    return {"message": "Welcome to Tea & Hive Backend 🍯!"}

# --- Test Database Endpoint (for quick verification) ---
@app.get("/test-db-endpoint/", summary="Test database connection", description="Verifies the database connection by requesting a session.")
def test_db_endpoint(db: Session = Depends(get_db)):
    return {"message": "This endpoint successfully accessed the database session."}

# --- Test Exception Endpoint (for quick verification of handlers) ---
# This endpoint is kept in main.py for easy testing of global handlers.
# In a real app, you might remove or move this to a dedicated 'dev' router.
@app.get("/test-error/{error_type}", summary="Test exception handler", description="Triggers different types of errors to test the global exception handler.")
def test_error_endpoint(error_type: str):
    from fastapi import HTTPException, status
    from fastapi.exceptions import RequestValidationError
    from pydantic import ValidationError # Imported locally for this specific test endpoint

    if error_type == "http":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This is a test HTTP error (Bad Request).")
    elif error_type == "generic":
        result = 1 / 0 # ZeroDivisionError
        return {"result": result}
    elif error_type == "validation":
        try:
            # Simulate a validation error
            user_schema.UserCreate(email="invalid", password="1", verify_password="1")
        except ValidationError as e:
            raise RequestValidationError(e.errors())
    else:
        return {"message": "Specify 'http', 'generic', or 'validation' to test errors."}

# --- How to Run ---
# 1. Ensure you are in the 'Hive-server' directory in your terminal.
# 2. Make sure your .env file is correctly configured.
# 3. Run the FastAPI application using uvicorn:
#    uvicorn main:app --reload
#    OR, if you have fastapi-cli installed:
#    fastapi dev main.py