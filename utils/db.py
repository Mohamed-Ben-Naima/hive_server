# Hive-server/utils/db.py

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging # <-- NEW: Import logging

# Get logger instance for this module
logger = logging.getLogger("tea_n_hive_logger.db") # Use a sub-logger for clarity

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=DEBUG_MODE # SQLAlchemy's echo will log SQL queries if DEBUG_MODE is True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed.") # Log session closing

def test_db_connection():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        logger.info("Database connection test successful within get_db.")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed within get_db: {e}") # Use logger.error
        return False
    finally:
        db.close()