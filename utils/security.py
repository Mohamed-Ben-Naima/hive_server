# hive_server/utils/security.py

# --- Standard Library Imports ---
from datetime import datetime, timedelta, timezone # <--- ADDED: timezone for UTC consistency
from typing import Optional, Annotated
import os
import logging

# --- External Library Imports ---
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# --- Internal Project Imports ---
from ..models.user import User as UserModel
from ..schemas.auth import TokenData
from ..utils.db import get_db
from ..utils.app_setup import ACCESS_TOKEN_EXPIRE_MINUTES, PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

# Get logger instance for this module
logger = logging.getLogger("tea_n_hive_logger.security")

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-that-is-at-least-32-chars-long")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Define the OAuth2PasswordBearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.
    Args:
        data (dict): The payload to encode into the token (e.g., {"sub": user_id}).
        expires_delta (Optional[timedelta]): Optional timedelta for token expiration.
    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta # Use timezone.utc for consistency
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # Use timezone.utc for consistency

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"JWT created with payload: {data}, expires at: {expire}")
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT access token.
    Args:
        token (str): The JWT token to decode.
    Returns:
        Optional[dict]: The decoded payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"JWT decoded successfully. Payload: {payload}")
        return payload
    except JWTError as e:
        logger.warning(f"JWT decoding failed: {e}")
        return None
    
def create_password_reset_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a special JWT for password reset.
    This token contains user_id and a 'purpose' claim.
    """
    to_encode = {"user_id": user_id, "purpose": "password_reset"}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta # Use timezone.utc for consistency
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Password reset JWT created for user_id: {user_id}, expires at: {expire}")
    return encoded_jwt

def decode_password_reset_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a password reset JWT.
    Checks for 'password_reset' purpose claim.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            logger.warning("Attempted to decode password reset token but 'purpose' claim is incorrect.")
            return None
        logger.debug(f"Password reset JWT decoded successfully. Payload: {payload}")
        return payload
    except JWTError as e:
        logger.warning(f"Password reset JWT decoding failed: {e}")
        return None

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> UserModel:
    """
    FastAPI dependency to get the current authenticated user from a JWT.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if payload is None:
            logger.warning("Attempted to access protected route with invalid/expired token.")
            raise credentials_exception

        token_data = TokenData(**payload)
        user_id = token_data.user_id
        if user_id is None:
            logger.warning("Token payload missing user_id.")
            raise credentials_exception

    except JWTError as e:
        logger.error(f"JWTError during get_current_user: {e}")
        raise credentials_exception
    except Exception as e:
        logger.exception(f"Unexpected error during get_current_user: {e}")
        raise credentials_exception

    from ..services.user import UserService # Imported here to avoid circular dependency
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if user is None:
        logger.warning(f"User with ID {user_id} not found from token.")
        raise credentials_exception

    logger.debug(f"User {user.email} (ID: {user.user_id}) successfully authenticated via JWT.")
    return user

# --- NEW: Optional Authentication Dependency ---
async def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme)], # Token is optional now
    db: Session = Depends(get_db)
) -> Optional[UserModel]:
    """
    FastAPI dependency to get the current authenticated user, or None if not authenticated.
    Does NOT raise HTTPException 401 if token is missing or invalid.
    """
    if token is None:
        logger.debug("Optional authentication: No token provided. Returning None.")
        return None # No token provided, so no authenticated user

    try:
        payload = decode_access_token(token)
        if payload is None:
            logger.warning("Optional authentication: Token is invalid/expired. Returning None.")
            return None # Token was present but invalid/expired

        token_data = TokenData(**payload)
        user_id = token_data.user_id
        if user_id is None:
            logger.warning("Optional authentication: Token payload missing user_id. Returning None.")
            return None # Token was present but invalid (no user_id)

    except JWTError as e:
        logger.warning(f"Optional authentication: JWT decoding failed: {e}. Returning None.")
        return None # Token was invalid
    except Exception as e:
        logger.exception(f"Optional authentication: Unexpected error during get_current_user_optional: {e}. Returning None.")
        return None

    from ..services.user import UserService # Imported here to avoid circular dependency
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if user is None:
        logger.warning(f"Optional authentication: User ID {user_id} from token not found in DB. Returning None.")
        return None # User from token not found in DB

    logger.debug(f"Optional authentication: User {user.email} (ID: {user.user_id}) found.")
    return user
# --- END NEW ---
