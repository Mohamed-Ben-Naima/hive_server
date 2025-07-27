# hive_server/utils/db.py

import os # Keep os for DEBUG_MODE check
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import logging

logger = logging.getLogger("tea_n_hive_logger.db")

# Global variables to hold the engine and SessionLocal after initialization
_engine = None
_SessionLocal = None

def initialize_db_engine(database_url: str):
    """
    Initializes the SQLAlchemy engine and SessionLocal.
    This function should be called once at application startup.
    """
    global _engine, _SessionLocal
    if not database_url:
        logger.critical("Database URL is missing or invalid. Cannot initialize DB engine.")
        raise ValueError("DATABASE_URL must be provided to initialize the database engine.")

    # Get DEBUG_MODE from environment for echo setting
    # We rely on load_dotenv being called in main.py before this function is called
    debug_mode = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    _engine = create_engine(database_url, echo=debug_mode)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    logger.info("SQLAlchemy engine and session factory initialized.")


def get_engine():
    """Returns the initialized SQLAlchemy engine."""
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call initialize_db_engine first.")
    return _engine

def get_session_local():
    """Returns the initialized SQLAlchemy SessionLocal factory."""
    if _SessionLocal is None:
        raise RuntimeError("Database session factory not initialized. Call initialize_db_engine first.")
    return _SessionLocal


def test_db_connection(db_url: str) -> bool: # db_url is a required parameter
    """
    Tests the database connection using the provided URL.
    Returns True if connection is successful, False otherwise.
    """
    if not db_url:
        logger.error("No DATABASE_URL provided for connection test.")
        return False

    try:
        # Create a temporary engine just for the test
        test_engine = create_engine(db_url, connect_args={"connect_timeout": 5}) # Add timeout
        with test_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection test successful within get_db.")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed within get_db: {e}")
        return False
    finally:
        # Ensure the test engine is disposed
        if '_engine' in locals() and test_engine: # Use 'test_engine' as it's local to this function
            test_engine.dispose()

def get_db():
    """Dependency to get a database session."""
    if _SessionLocal is None:
        raise RuntimeError("Database session factory not initialized. Call initialize_db_engine first.")

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed.")
