# hive_server/utils/file_manager.py

import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4 # For generating unique filenames

from dotenv import load_dotenv # To load environment variables
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger("tea_n_hive_logger.file_manager")

# Load environment variables at the very top of this utility file.
# This ensures that UPLOAD_DIRECTORY_PATH is available when the module is imported.
load_dotenv()

# --- Configuration for Uploads ---
# Define the base directory for uploads from an environment variable.
# Provides a sensible default for local development if the env var is not set.
UPLOAD_DIRECTORY_PATH = os.getenv("UPLOAD_DIRECTORY_PATH", "uploads")
UPLOAD_DIRECTORY = Path(UPLOAD_DIRECTORY_PATH)

# Ensure the upload directory exists when this module is imported.
# This runs once at application startup.
try:
    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory ensured: {UPLOAD_DIRECTORY.absolute()}")
except OSError as e:
    logger.critical(f"Failed to create upload directory {UPLOAD_DIRECTORY.absolute()}: {e}")
    # In a utility file, we log the critical error. The application's lifespan manager
    # (in app_setup.py) should handle fatal errors like this if the directory is truly
    # essential for startup.


async def save_upload_file(media_file: UploadFile) -> str:
    """
    Saves an uploaded file to the UPLOAD_DIRECTORY with a unique filename.

    Args:
        media_file (UploadFile): The file object received from FastAPI.

    Returns:
        str: The unique filename (e.g., "my_image_abc123.jpg") stored in the UPLOAD_DIRECTORY.
             This filename is what should be saved in the database.

    Raises:
        HTTPException: If the file cannot be saved.
    """
    # --- CRITICAL FIX: Robust Empty File Input Handling ---
    # This specifically handles cases where FastAPI might receive an empty string
    # for an Optional[UploadFile] field (e.g., from curl -F 'field=' or Swagger UI
    # when no file is selected), or an UploadFile object with an empty filename.
    # This is crucial for compatibility with various clients.
    if isinstance(media_file, str) and not media_file:
        logger.debug("Received empty string for media_file, treating as no file.")
        return None # Return None if no actual file content is provided
    if media_file and not media_file.filename:
        logger.debug("Received UploadFile with empty filename, treating as no file.")
        return None # Return None if UploadFile object exists but has no filename
    # --- END CRITICAL FIX ---

    # Original check for missing filename (now applies after robust handling)
    if not media_file.filename:
        logger.warning("Attempted to save an uploaded file with no filename after initial checks.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename."
        )

    # Extract original file extension
    file_extension = media_file.filename.split(".")[-1] if "." in media_file.filename else ""
    # Generate a unique filename using UUID to prevent collisions
    unique_filename = f"{uuid4().hex}.{file_extension}" if file_extension else uuid4().hex
    
    # Construct the full path where the file will be saved
    file_path = UPLOAD_DIRECTORY / unique_filename

    try:
        # Read the entire file content asynchronously and write to disk.
        contents = await media_file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        logger.info(f"File '{media_file.filename}' saved as '{unique_filename}' to '{file_path.absolute()}'.")
        return unique_filename # Return only the unique filename
    except Exception as e:
        logger.exception(f"Failed to save uploaded file '{media_file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save media file: {e}"
        )
    finally:
        # Ensure the uploaded file stream is closed, releasing resources.
        await media_file.close()


def delete_file(filename: str) -> bool:
    """
    Deletes a file from the UPLOAD_DIRECTORY.

    Args:
        filename (str): The unique filename of the file to delete (e.g., "my_image_abc123.jpg").

    Returns:
        bool: True if the file was successfully deleted or didn't exist, False on other errors.
    """
    if not filename:
        logger.warning("Attempted to delete a file with an empty filename.")
        return False

    file_path = UPLOAD_DIRECTORY / filename
    
    # Check if the file exists before attempting to delete.
    if not file_path.exists():
        logger.info(f"Attempted to delete file '{filename}', but it does not exist at '{file_path.absolute()}'.")
        return True # Consider it successful if it's already gone

    try:
        os.remove(file_path) # Perform the actual file deletion.
        logger.info(f"Successfully deleted file: '{filename}' from '{file_path.absolute()}'.")
        return True
    except OSError as e:
        logger.error(f"Failed to delete file '{filename}' from '{file_path.absolute()}': {e}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred while deleting file '{filename}': {e}")
        return False
