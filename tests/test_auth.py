# hive_server/tests/test_auth.py

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# --- FIX: All imports are now absolute from the 'hive_server' package ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from ..utils.db import get_db
from ..models.base import Base
from ..models.user import User, Profile

# --- Test Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def db_session_fixture():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client")
async def client_fixture(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

# --- Registration Test Cases ---

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "StrongP@ss1",
            "verify_password": "StrongP@ss1"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["profile"]["username"] == "testuser"
    assert "user_id" in data
    assert "profile_id" in data["profile"]
    assert data["message"] == "User registered successfully!"
    assert data["last_login"] is None

@pytest.mark.asyncio
async def test_register_user_existing_email(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "username": "existinguser",
            "password": "StrongP@ss1",
            "verify_password": "StrongP@ss1"
        }
    )

    response = await client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "username": "anotheruser",
            "password": "StrongP@ss2",
            "verify_password": "StrongP@ss2"
        }
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Email already registered"

@pytest.mark.asyncio
async def test_register_user_existing_username(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "user1@example.com",
            "username": "uniqueusername",
            "password": "StrongP@ss1",
            "verify_password": "StrongP@ss1"
        }
    )

    response = await client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "username": "uniqueusername",
            "password": "StrongP@ss2",
            "verify_password": "StrongP@ss2"
        }
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Username already taken"

@pytest.mark.asyncio
async def test_register_user_invalid_email_format(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "username": "validuser",
            "password": "StrongP@ss1",
            "verify_password": "StrongP@ss1"
        }
    )
    assert response.status_code == 422
    assert "Validation error" in response.json()["message"]
    assert "Field 'email': value is not a valid email address" in response.json()["details"]

@pytest.mark.asyncio
async def test_register_user_weak_password(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "weakpass@example.com",
            "username": "weakpassuser",
            "password": "weak",
            "verify_password": "weak"
        }
    )
    assert response.status_code == 422
    assert "Validation error" in response.json()["message"]
    assert "Field 'password': Password must be at least 8 characters long" in response.json()["details"][0]

@pytest.mark.asyncio
async def test_register_user_mismatched_passwords(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "mismatch@example.com",
            "username": "mismatchuser",
            "password": "StrongP@ss1",
            "verify_password": "StrongP@ss2"
        }
    )
    assert response.status_code == 422
    assert "Validation error" in response.json()["message"]
    assert "Field 'verify_password': Passwords do not match." in response.json()["details"]

@pytest.mark.asyncio
async def test_register_user_empty_username(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "emptyuser@example.com",
            "username": "",
            "password": "StrongP@ss1",
            "verify_password": "StrongP@ss1"
        }
    )
    assert response.status_code == 422
    assert "Validation error" in response.json()["message"]
    assert "Field 'username': Username cannot be empty or just spaces." in response.json()["details"]

@pytest.mark.asyncio
async def test_register_user_username_with_spaces(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "spaceuser@example.com",
            "username": "user with spaces",
            "password": "StrongP@ss1",
            "verify_password": "StrongP@ss1"
        }
    )
    assert response.status_code == 422
    assert "Validation error" in response.json()["message"]
    assert "Field 'username': Username cannot contain spaces." in response.json()["details"]