# Hive-server/database.py

import os
from sqlalchemy import create_engine, text # <-- NEW: Import 'text' for a simple query
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve database credentials from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

# Construct the database URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False # Set to False for cleaner output, we'll print our own success message
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models (still needed if you plan models later)
#Base = declarative_base()

# Dependency to get a database session for FastAPI
def get_db():
    db = SessionLocal()
    try:
        # Attempt a simple query to verify the connection
        # This is a lightweight way to check if the database is reachable and credentials are valid.
        db.execute(text("SELECT 1"))
        print("\n✅ Database connection successful! ✅\n")
        yield db
    except Exception as e:
        print(f"\n❌ Database connection FAILED: {e} ❌\n")
        # Re-raise the exception to propagate the error to FastAPI
        raise
    finally:
        db.close()

# print("Attempting direct database connection test...")
# try:
#     db_session = next(get_db())
# except Exception:
#     pass
# print("Done")