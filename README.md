Tea & Hive Backend Server
Welcome to the backend server for the Tea & Hive application!
This project is built with FastAPI and provides a robust, scalable, and secure API for managing core functionalities like user authentication and profiles.

🌟 Key Features
Robust User Registration:

Secure account creation with email, unique username, and strong password.

Comprehensive validation for email format, username uniqueness (no spaces, not empty), and password complexity.

Atomic creation of User and Profile records for data consistency.

Clear success messages on registration.

Secure User Login & JWTs:

Dedicated POST /auth/token endpoint for user authentication.

Issues industry-standard JWT (JSON Web Tokens) for secure API access.

Returns essential user details (ID, email, username) directly with the token for client convenience.

Updates last_login timestamp on successful login for auditing.

Current User Profile Retrieval:

GET /users/me endpoint to fetch the detailed profile of the currently authenticated user.

Leverages JWT validation and eager-loading of user profile data for efficiency.

Update Current User Profile:

PATCH /users/me/update endpoint allowing authenticated users to partially update their own profile details (e.g., first name, bio, trading style, social links).

Uses a dedicated ProfileUpdate schema, ensuring only provided fields are modified, leaving others untouched.

Includes server-side validation for username uniqueness during updates.

Change Password (Authenticated User):

POST /users/me/password endpoint enabling authenticated users to securely change their password.

Requires the user to provide their current password for verification before setting a new one.

Includes robust validation for the new password, ensuring complexity, confirmation matching, and that the new password is not identical to the current one.

Layered Architecture:

Clean separation into routers, controllers, services, models, schemas, and utils for maintainability, testability, and clear separation of concerns.

Global Exception Handling:

Consistent, user-friendly JSON error responses for validation errors, HTTP errors, and unexpected server errors.

Sophisticated Logging:

Integrated Python logging for structured, configurable output, aiding in debugging and monitoring.

Environment Variable Management:

Secure handling of sensitive configuration using .env files (e.g., database credentials, JWT secret keys).

Comprehensive Testing Setup:

Initial setup for pytest and httpx with an in-memory SQLite database for fast, isolated tests.

🏗️ Architecture Overview
The backend follows a layered architecture for modularity and testability:

routers/: Defines API endpoints and maps requests to appropriate controllers. (Handles request/response flow).

controllers/: Orchestrates business logic by coordinating between services and preparing responses. (Contains the "what to do" logic).

services/: Encapsulates core business logic and interacts directly with the database via SQLAlchemy ORM. (Abstracts data access).

models/: SQLAlchemy ORM models defining the structure of database tables (e.g., User, Profile).

schemas/: Pydantic models for request body validation, query parameters, and response serialization.

utils/: Helper functions, middleware, application setup, security utilities (JWT, password hashing), and database connection management.

tests/: Automated tests for server functionality.

uploads/: Placeholder for file uploads (e.g., avatars).

📁 Project Structure
.
└── hive_server/              # Main backend application package
    ├── .env                  # Environment variables (DO NOT COMMIT!)
    ├── __init__.py           # Makes 'hive_server' a Python package
    ├── main.py               # FastAPI application entry point
    ├── controllers/
    │   ├── __init__.py       # Python package marker
    │   ├── auth.py           # Authentication-related controllers (login, register)
    │   └── user.py           # User-related controllers (get current user, update profile, change password)
    ├── models/
    │   ├── __init__.py       # Python package marker
    │   ├── base.py           # SQLAlchemy declarative base
    │   └── user.py           # User and Profile ORM models
    ├── routers/
    │   ├── __init__.py       # Python package marker
    │   ├── auth.py           # Authentication API routes (/auth/register, /auth/token)
    │   └── users.py          # User API routes (/users/me, /users/me/update, /users/me/password)
    ├── schemas/
    │   ├── __init__.py       # Python package marker
    │   ├── auth.py           # Pydantic schemas for authentication (Token, TokenData)
    │   └── user.py           # Pydantic schemas for User/Profile data (UserCreate, ProfileUpdate, PasswordChange, UserResponse, ProfileResponse, UserWithProfileResponse, UserForTokenResponse)
    ├── services/
    │   ├── __init__.py       # Python package marker
    │   └── user.py           # Business logic for user operations (create, authenticate, update profile, change password)
    ├── tests/
    │   ├── __init__.py       # Python package marker
    │   └── test_auth.py      # Tests for authentication (registration, login)
    ├── uploads/
    │   ├── __init__.py       # Python package marker
    │   ├── avatars/
    │   │   └── __init__.py   # Python package marker
    │   └── temp/
    │       └── __init__.py   # Python package marker
    └── utils/
        ├── __init__.py       # Python package marker
        ├── app_setup.py      # App setup (lifespan, middleware, logging)
        ├── db.py             # Database connection/session management
        └── security.py       # Password hashing, JWT utilities

🛠️ Technologies Used
Backend Framework: FastAPI

ASGI Server: Uvicorn

Database: PostgreSQL (dev/prod), SQLite (testing)

ORM: SQLAlchemy

Database Driver: psycopg2-binary

Data Validation: Pydantic

Password Hashing: Passlib (with bcrypt backend)

Environment Variables: python-dotenv

HTTP Client (tests): httpx

Testing: pytest

Other: logging, os, re, datetime, typing, contextlib, traceback, sys, python-multipart (for form data handling if needed, implicitly by FastAPI).

📦 Requirements
Add these to your requirements.txt file in the root of your project (e.g., Hive-app/requirements.txt):

fastapi
uvicorn
SQLAlchemy
psycopg2-binary
python-dotenv
pydantic
pydantic-settings
passlib
python-jose
python-multipart
httpx
pytest

🚀 Setup and Installation
Prerequisites
Python 3.7+ (recommended: Python 3.9+)

PostgreSQL database instance (local or cloud)

1. Clone the Repository
git clone <your-repo-url>
# Navigate to the parent directory of 'hive_server', which is your project root (e.g., 'Hive-app/')
cd Hive-app

2. Create a Virtual Environment
It's recommended to create the virtual environment in the project root (Hive-app/).

python -m venv .venv
# On Windows
.\.venv\Scripts\activate
# On macOS/Linux
source ./.venv/bin/activate

3. Install Dependencies
With your virtual environment activated, install the required packages:

pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the hive_server/ directory (the same directory as main.py):

# .env file (inside hive_server directory)

# Database Configuration
DB_HOST=localhost            # e.g., localhost, 127.0.0.1, or a cloud connection string
DB_NAME=your_database_name
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_PORT=5432

# Application Configuration
DEBUG_MODE=True              # Set to False for production. Enables SQLAlchemy echo and debug logs.
SECRET_KEY="a_very_long_and_random_secret_key_for_your_application_0123456789abcdef"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration (optional, if you want to override defaults from app_setup.py)
# CORS_ORIGINS=["http://localhost:3000", "https://yourfrontend.com"]
# CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
# CORS_HEADERS=["*"]

Important: Replace placeholders (your_database_name, your_db_username, etc.) with your actual credentials. Never commit your .env file to version control.

5. Database Setup (PostgreSQL)
Ensure your PostgreSQL database is running and accessible.
If you have an existing SQL schema (e.g., teanhive.sql), you can set up your database using your PostgreSQL client:

psql -h your_db_host -p 5432 -U your_db_username -d your_database_name -f path/to/teanhive.sql

Manual Schema Updates (Development Only):
If you add new fields to your SQLAlchemy models (e.g., is_active to the User model, or last_jti), you will need to update your database schema. For development purposes without a migration tool (like Alembic), you can manually run SQL ALTER TABLE commands in your PostgreSQL client:

-- Example: Adding 'is_active' to the users table
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Example: Adding 'last_jti' to the users table
ALTER TABLE users ADD COLUMN last_jti VARCHAR(255) NULL;

Warning: This manual approach is not recommended for production environments with existing data. For production, a proper database migration tool (like Alembic) should be used.

▶️ Running the Server
Make sure your virtual environment is activated.

Option A: Using fastapi dev (Recommended for Development)
This is the most convenient way to run your server during development, as it handles reloading and environment setup effectively.

# Navigate to the 'hive_server' directory
cd C:\Users\ASUS\Desktop\Hive\Hive-app\hive_server
fastapi dev main.py

Option B: Using uvicorn (For Production or Specific Testing)
If you need to run with uvicorn directly, ensure you are in the project's root directory (Hive-app/) for uvicorn to correctly locate your application package and environment files.

# Navigate to the project root (e.g., 'Hive-app/')
cd C:\Users\ASUS\Desktop\Hive\Hive-app
uvicorn --app-dir . hive_server.main:app --reload

The --reload flag will automatically restart the server when code changes are detected.

Once the server is running, you can access the interactive API documentation (Swagger UI) at:
http://127.0.0.1:8000/docs

🧪 Running Tests
Ensure your virtual environment is activated. You should be in the parent directory of hive_server (e.g., Hive-app/).

cd C:\Users\ASUS\Desktop\Hive\Hive-app
pytest hive_server/tests/

All tests use an in-memory SQLite database for speed and isolation.

🛣️ Next Steps & Future Enhancements
Database Migrations (Alembic): Integrate Alembic for managing database schema changes in a version-controlled and safe way, especially for production environments.

Refresh Tokens & Token Revocation: Enhance security and user experience by implementing refresh tokens and a token blacklist (e.g., using the last_jti field) to invalidate old tokens upon new logins or password changes.

Email Verification: Implement a flow to verify user email addresses, potentially using an is_active field on the User model to restrict access until verified.

Password Recovery (Forgot Password): Implement a secure flow for users to reset their password if they forget it (e.g., via email link).

User Deactivation/Deletion: Provide functionality for users to deactivate or delete their accounts.

Core Trading Functionality: Implement features like trade logging, performance analysis, challenges, and reports.

Social Features: Develop endpoints for posts, comments, and likes.

Shorts System: Build out the short video content features.