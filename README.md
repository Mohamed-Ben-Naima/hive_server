Trader Hive Backend Server
Welcome to the backend server for the Trader Hive application!
This project is built with FastAPI and provides a robust, scalable, and secure API for managing core functionalities like user authentication and profiles.

🌟 Key Features
Robust User Registration:

Secure account creation with email, unique username, and strong password.

Comprehensive validation for email format, username uniqueness (no spaces, not empty), and password complexity.

Atomic creation of User and Profile records for data consistency.

Clear success messages on registration.

Layered Architecture:

Clean separation into routers, controllers, services, models, schemas, and utils for maintainability.

Global Exception Handling:

Consistent, user-friendly JSON error responses for validation errors, HTTP errors, and unexpected server errors.

Sophisticated Logging:

Integrated Python logging for structured, configurable output.

Environment Variable Management:

Secure handling of sensitive configuration using .env files.

Comprehensive Testing:

Setup for pytest and httpx with an in-memory SQLite database for fast, isolated tests.

🏗️ Architecture Overview
The backend follows a layered architecture for modularity and testability:

routers/: API endpoints and mapping to controllers.

controllers/: Orchestrate business logic and request/response flow.

services/: Core business logic and database operations.

models/: SQLAlchemy ORM models for database tables.

schemas/: Pydantic models for request validation and response serialization.

utils/: Helper functions, middleware, app setup, security, and DB connection.

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
    │   └── auth.py           # Authentication-related controllers
    ├── models/
    │   ├── __init__.py       # Python package marker
    │   ├── base.py           # SQLAlchemy declarative base
    │   └── user.py           # User and Profile ORM models
    ├── routers/
    │   ├── __init__.py       # Python package marker
    │   └── auth.py           # Authentication API routes
    ├── schemas/
    │   ├── __init__.py       # Python package marker
    │   └── user.py           # Pydantic schemas for User/Profile data
    ├── services/
    │   ├── __init__.py       # Python package marker
    │   └── user.py           # Business logic for user operations
    ├── tests/
    │   ├── __init__.py       # Python package marker
    │   └── test_auth.py      # Tests for authentication (registration)
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
        └── security.py       # Password hashing utilities

🛠️ Technologies Used
Backend Framework: FastAPI

ASGI Server: Uvicorn

Database: PostgreSQL (dev/prod), SQLite (testing)

ORM: SQLAlchemy

Database Driver: psycopg2-binary

Data Validation: Pydantic

Password Hashing: Passlib (bcrypt)

Env Variables: python-dotenv

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
# Navigate to the parent directory of 'Hive-server', e.g., 'Hive-app/'
cd Hive-app # Or wherever 'Hive-server' is located

2. Create a Virtual Environment
Navigate into the hive_server directory first, then create the virtual environment.

cd hive_server
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the hive_server/ directory (the same directory as main.py):

DB_HOST=your_db_host_ip_or_connection_name # e.g., localhost, 127.0.0.1, or a cloud connection string
DB_NAME=your_database_name
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_PORT=5432
DEBUG_MODE=True # Set to False for production. Enables SQLAlchemy echo and debug logs.
SECRET_KEY=a_very_long_and_random_secret_key_for_your_application_0123456789abcdef

Important: Replace placeholders with your actual credentials.
Never commit your .env file to version control.

5. Database Setup (PostgreSQL)
Ensure your PostgreSQL database is running and accessible.
If you have a SQL schema file (e.g., teanhive.sql), you can set up your database with:

psql -h your_db_host -p 5432 -U your_db_username -d your_database_name -f path/to/teanhive.sql

▶️ Running the Server
Make sure your virtual environment is activated. You should be in the parent directory of hive_server (e.g., Hive-app/).

# From the directory containing 'Hive-server'
uvicorn Hive-server.main:app --reload

# From the 'Hive-server' directory 
fastapi dev main.py

# OR, if you have fastapi-cli installed, from the same parent directory:
fastapi dev Hive-server/main.py

The --reload flag will automatically restart the server when code changes are detected.

Once the server is running, you can access the interactive API documentation (Swagger UI) at:
http://127.0.0.1:8000/docs

🧪 Running Tests
Ensure your virtual environment is activated. You should be in the parent directory of hive_server (e.g., Hive-app/).

pytest Hive-server/tests/

All tests use an in-memory SQLite database for speed and isolation.

🛣️ Next Steps & Future Enhancements
User Authentication (Login & JWTs): Implement login functionality and secure API access using JSON Web Tokens.

Database Migrations (Alembic): Integrate Alembic for managing database schema changes in a version-controlled way.

User Profile Management: Develop endpoints for updating user profile details.

Core Trading Functionality: Implement features like trade logging, performance analysis, challenges, and reports.

Social Features: Develop endpoints for posts, comments, and likes.

Shorts System: Build out the short video content features.