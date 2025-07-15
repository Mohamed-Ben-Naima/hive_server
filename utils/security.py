# hive_server/utils/security.py

# --- Standard Library Imports ---
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

# --- External Library Imports ---
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session # For type hinting in get_current_user

# --- Internal Project Imports ---
# These can be imported at the top because they don't create circular dependencies
from ..models.user import User # User model for type hinting
from ..schemas.auth import TokenData # Schema for JWT payload
from ..utils.db import get_db # Database session dependency


# Get logger instance for this module
logger = logging.getLogger("tea_n_hive_logger.security")

# --- Password Hashing ---
# Use bcrypt algorithm for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Configuration ---
# Retrieve SECRET_KEY and ALGORITHM from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-that-is-at-least-32-chars-long")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Define the access token expiration time in minutes
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # <--- ADD THIS LINE

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
        expire = datetime.utcnow() + expires_delta
    else:
        # Use the global ACCESS_TOKEN_EXPIRE_MINUTES if no specific delta is provided
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) 

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

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
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

    # IMPORTANT: UserService must be imported here to avoid circular dependency
    # because UserService imports security.py
    from ..services.user import UserService
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if user is None:
        logger.warning(f"User with ID {user_id} not found from token.")
        raise credentials_exception

    logger.debug(f"User {user.email} (ID: {user.user_id}) successfully authenticated via JWT.")
    return user
