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

Returns essential user details (ID, email, username, active status) directly with the token for client convenience.

Updates last_login timestamp on successful login for auditing.

Current User Profile Retrieval:

GET /users/me endpoint to fetch the detailed profile of the currently authenticated user.

Leverages JWT validation and eager-loading of user profile data for efficiency.

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
└── hive_server/              # Main backend application package (renamed from Hive-server)
    ├── .env                  # Environment variables (DO NOT COMMIT!)
    ├── __init__.py           # Makes 'hive_server' a Python package
    ├── main.py               # FastAPI application entry point
    ├── controllers/
    │   ├── __init__.py       # Python package marker
    │   ├── auth.py           # Authentication-related controllers (login, register)
    │   └── user.py           # User-related controllers (e.g., get current user)
    ├── models/
    │   ├── __init__.py       # Python package marker
    │   ├── base.py           # SQLAlchemy declarative base
    │   └── user.py           # User and Profile ORM models
    ├── routers/
    │   ├── __init__.py       # Python package marker
    │   ├── auth.py           # Authentication API routes (/auth/register, /auth/token)
    │   └── users.py          # User API routes (/users/me)
    ├── schemas/
    │   ├── __init__.py       # Python package marker
    │   ├── auth.py           # Pydantic schemas for authentication (Token, TokenData)
    │   └── user.py           # Pydantic schemas for User/Profile data (UserCreate, UserResponse, ProfileResponse, UserWithProfileResponse, UserForTokenResponse)
    ├── services/
    │   ├── __init__.py       # Python package marker
    │   └── user.py           # Business logic for user operations
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

Other: logging, os, re, datetime, typing, contextlib, traceback, sys.

📦 Requirements
Add these to your requirements.txt file in the hive_server/ directory:

fastapi
uvicorn
sqlalchemy
psycopg2-binary
python-dotenv
pydantic[email] # Includes email-validator
passlib[bcrypt]
python-multipart
httpx
pytest

🚀 Setup and Installation
Prerequisites
Python 3.7+ (recommended: Python 3.9+)

PostgreSQL database instance (local or cloud)

1. Clone the Repository
git clone <your-repo-url>
# Navigate to the parent directory of 'hive_server', e.g., 'Hive-app/'
cd Hive-app

2. Create a Virtual Environment
Navigate into the hive_server directory first, then create the virtual environment.

cd hive_server
python -m venv .venv
# On Windows
.\.venv\Scripts\activate
# On macOS/Linux
source ./.venv/bin/activate

3. Install Dependencies
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

Important: Replace placeholders (your_db_host_ip_or_connection_name, etc.) with your actual credentials.
Never commit your .env file to version control.

5. Database Setup (PostgreSQL)
Ensure your PostgreSQL database is running and accessible.
If you have a SQL schema file (e.g., teanhive.sql), you can set up your database with:

psql -h your_db_host -p 5432 -U your_db_username -d your_database_name -f path/to/teanhive.sql

▶️ Running the Server
Make sure your virtual environment is activated.

Option A: From the parent directory of hive_server (e.g., Hive-app/)
This is the recommended way to run when your application is a package.

cd C:\Users\ASUS\Desktop\Hive\Hive-app
uvicorn --app-dir . hive_server.main:app --reload

Option B: From inside the hive_server directory (Recommended)
This option works if you prefer to be directly in the application's root.

cd C:\Users\ASUS\Desktop\Hive\Hive-app\hive_server
fastapi dev main.py

The --reload flag will automatically restart the server when code changes are detected.

Once the server is running, you can access the interactive API documentation (Swagger UI) at:
http://127.0.0.1:8000/docs

🧪 Running Tests
Ensure your virtual environment is activated. You should be in the parent directory of hive_server (e.g., Hive-app/).

cd C:\Users\ASUS\Desktop\Hive\Hive-app
pytest hive_server/tests/

All tests use an in-memory SQLite database for speed and isolation.

🛣️ Next Steps & Future Enhancements
Resolve Database Connection Issue: This is the most critical immediate next step to ensure all database-dependent functionalities work correctly.

User Profile Management: Develop endpoints for updating user profile details (PUT/PATCH /users/me).

Password Change Functionality: Implement a secure way for authenticated users to change their password.

Database Migrations (Alembic): Integrate Alembic for managing database schema changes in a version-controlled way.

Core Trading Functionality: Implement features like trade logging, performance analysis, challenges, and reports.

Social Features: Develop endpoints for posts, comments, and likes.

Shorts System: Build out the short video content features.

Refresh Tokens & Token Revocation: Enhance security and user experience by implementing refresh tokens and a token blacklist.