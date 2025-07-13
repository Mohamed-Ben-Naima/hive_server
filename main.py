from typing import Union
from fastapi import FastAPI
from .database import get_db
from contextlib import asynccontextmanager # <-- NEW: Import asynccontextmanager


# --- NEW: Define the lifespan context manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event logic
    print("\nAttempting database connection test on server startup...")
    try:
        # Use 'next()' on the generator to execute the connection test
        db_session = next(get_db())
        db_session.close() # Ensure the session is closed immediately after test
        print("✅ Database connection successful on startup! ✅")
    except Exception as e:
        print(f"❌ Database connection FAILED on startup: {e} ❌")
        # In a production app, you might want to exit here if DB is critical
        # import sys
        # sys.exit(1)
    yield # Application starts here
    # Shutdown event logic (optional, for cleanup if needed)
    print("\nFastAPI application shutting down.")


# Pass the lifespan to the FastAPI instance
app = FastAPI(
    title="Trader Hive Backend",
    description="API for Trader Hive mobile application.",
    version="0.1.0",
    lifespan=lifespan # <-- NEW: Register the lifespan
)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI bishh!"}

@app.get("/hive")
def read_hive():
    return {"message": "Hello, from Hive! 🐝 🍯"}