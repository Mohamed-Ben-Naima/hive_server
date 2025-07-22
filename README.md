Tea & Hive Backend API 🍯
Table of Contents
About Tea & Hive

Features

Technologies Used

Getting Started

Prerequisites

Installation

Environment Variables

Database Setup

Running the Application

API Documentation (Swagger UI)

Project Structure

Best Practices & Design Principles

Testing

Contributing

License

Contact

1. About Tea & Hive
The Tea & Hive Backend API serves as the robust foundation for a modern social media and trading community application. It is designed to be scalable, secure, and maintainable, providing core functionalities for user management, social interactions (posts, likes, comments), and future expansion into trading challenges and educational content. Built with FastAPI and SQLAlchemy, it leverages best-in-class Python technologies for high performance and developer experience.

2. Features
The current iteration of the Tea & Hive Backend API includes the following core functionalities:

User Management:

User registration with secure password hashing.

User authentication (login) with JWT (JSON Web Tokens).

Retrieval of user profiles.

Password reset functionality.

Update user profile details (e.g., first name, bio, trading style, social links).

Change password for authenticated users.

Post Management:

Full CRUD Operations: Create, retrieve (single, all, paginated), update, and delete posts.

Flexible Content Types: Support for TEXT, IMAGE, and VIDEO post types with dynamic content validation.

Media File Uploads: Robust handling of image and video file uploads to the local file system, with dynamic URL generation for client access.

Content Validation: Enforces rules like "TEXT posts must have text content and no media," and "IMAGE/VIDEO posts need at least text or media."

Enhanced Post Response Data: When fetching posts, the API now includes:

likes_count: The total number of likes a post has received.

is_liked_by_current_user: A boolean indicating if the currently authenticated user has liked that specific post (returns false for unauthenticated users).

comments_count: The total number of comments a post has received, efficiently calculated and included in the response.

Post Likes:

Like and Unlike Posts: Authenticated users can like and unlike posts.

Unique Liking: Enforces a unique constraint ensuring a user can like a post only once.

Retrieve Likes for a Post: Get a paginated list of users who liked a specific post.

Retrieve Posts Liked by User: Get a paginated list of posts that a specific user has liked.

created_at Timestamp: Each like now includes a created_at timestamp, providing valuable auditability.

Post Comments:

Full CRUD Operations: Create, retrieve (single, all for a post, paginated), update, and delete comments on posts.

Ownership Checks: Ensures only the comment's author can update or delete their comment.

User Information: Comment responses include details about the user who made the comment.

Authentication & Authorization:

JWT-based authentication for secure API access.

Dependencies for required authentication (get_current_user) and optional authentication (get_current_user_optional) for public endpoints that can provide personalized data if a user is logged in.

Centralized Utilities:

Database connection management.

Centralized and configurable logging.

Global exception handling for consistent API error responses.

Environment variable management for flexible configuration.

3. Technologies Used
Backend Framework: FastAPI (Python) - For building high-performance APIs.

ASGI Server: Uvicorn - Powers FastAPI applications.

Database: PostgreSQL - Robust, open-source relational database.

ORM (Object-Relational Mapper): SQLAlchemy - For interacting with the database using Python objects.

Data Validation & Serialization: Pydantic - For defining data schemas and automatic validation.

Password Hashing: Passlib - For secure password storage (using bcrypt).

JWT Handling: python-jose - For JSON Web Token creation and verification.

Environment Variables: python-dotenv - For loading configuration from .env files.

File System Operations: Python's built-in os and pathlib.

HTTP Client (for tests): httpx

Testing Framework: pytest

Other: python-multipart (for form data handling, implicitly by FastAPI).

4. Getting Started
Follow these steps to set up and run the Tea & Hive Backend API on your local machine.

Prerequisites
Python 3.11+

PostgreSQL Database: Ensure you have a PostgreSQL server running and accessible.

Installation
Clone the repository:

git clone https://github.com/Meeeeedd/hive_server.git
cd hive_server # Navigate to the hive_server directory

Create and activate a Python virtual environment:

python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source ./.venv/bin/activate

Install dependencies:
Create a requirements.txt file in your project root (e.g., hive_server/) with the following content:

fastapi==0.111.0
uvicorn[standard]==0.30.1
SQLAlchemy==2.0.30
psycopg2-binary==2.9.9
python-dotenv==1.0.1
pydantic==2.7.4
pydantic-settings==2.3.4
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.9
httpx==0.27.0
pytest==8.2.2

Then install:

pip install -r requirements.txt

Environment Variables
Create a .env file in the hive_server/ directory (the same directory as main.py) with the following variables. Replace placeholder values with your actual credentials and settings.

# Database Configuration
DATABASE_URL="postgresql://user:password@host:port/database_name"
# Example: DATABASE_URL="postgresql://teanhive_user:mysecretpassword@localhost:5432/teanhive_db"

# Application Settings
SECRET_KEY="your-super-secret-key-that-is-at-least-32-chars-long-and-random-string"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=5
APP_VERSION="1.0.0" # Or current version
DEBUG_MODE="True" # Set to "False" for production. Enables SQLAlchemy echo and debug logs.

# CORS Configuration (adjust for your frontend's origin)
CORS_ORIGINS="http://localhost:3000,https://your-frontend-domain.com" # Comma-separated list of allowed origins or "*" for all
CORS_METHODS="GET,POST,PUT,DELETE,PATCH,OPTIONS" # Allowed HTTP methods
CORS_HEADERS="*" # Allowed headers

# File Uploads
UPLOAD_DIRECTORY_PATH="uploads" # Directory where media files will be stored (relative to hive_server)
BASE_URL="http://localhost:8000" # Base URL for your API, used for generating media links

Important: Replace placeholders (e.g., your_database_name, your_db_username, your-super-secret-key-that-is-at-least-32-chars-long-and-random-string) with your actual credentials. Never commit your .env file to version control.

Database Setup
Ensure your PostgreSQL server is running.

Create the database and user as specified in your DATABASE_URL.

Run the SQL schema script to create all necessary tables:

# Assuming teanhive.sql is in your project root (e.g., 'hive_server/')
psql -U your_db_user -d your_db_name -h your_db_host -p your_db_port -f teanhive.sql

Replace your_db_user, your_db_name, your_db_host, your_db_port with your actual database credentials.

Manual Schema Updates (Development Only):
If you add new fields or tables to your SQLAlchemy models, you will need to update your database schema. For development purposes without a migration tool (like Alembic), you can manually run SQL ALTER TABLE or CREATE TABLE commands in your PostgreSQL client.

For post_likes table (if created_at was missing):

ALTER TABLE post_likes
ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

For post_comments table:

CREATE TABLE "post_comments" (
    "comment_id" SERIAL PRIMARY KEY,
    "post_id" INT NOT NULL REFERENCES "posts"("post_id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "text_content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

Warning: This manual approach is not recommended for production environments with existing data. For production, a proper database migration tool (like Alembic) should be used.

Running the Application
Make sure your virtual environment is activated.

# Navigate to the hive_server directory
cd C:\Users\ASUS\Desktop\Hive\Hive-app\hive_server

# Run using fastapi dev
fastapi dev main.py

The API will be accessible at http://localhost:8000.

5. API Documentation (Swagger UI)
After running the application, you can access the interactive API documentation (Swagger UI) at:
http://localhost:8000/docs

This interface allows you to explore all available endpoints, their parameters, expected responses, and even make direct API calls for testing.

6. Project Structure
The project follows a modular and layered architecture:

your_root_directory/
├── .env                        # Environment variables (DO NOT COMMIT!)
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── teanhive.sql                # Database schema DDL
└── hive_server/                # Main backend application package
    ├── __init__.py
    ├── main.py                 # FastAPI application entry point
    ├── models/                 # SQLAlchemy ORM models (database schema)
    │   ├── __init__.py
    │   ├── base.py             # SQLAlchemy declarative base
    │   ├── user.py             # User and Profile models
    │   ├── posts.py            # Post model
    │   ├── post_likes.py       # PostLike model
    │   └── post_comments.py    # PostComment model (NEW)
    ├── schemas/                # Pydantic models (request/response data validation)
    │   ├── __init__.py
    │   ├── auth.py             # Authentication-related schemas
    │   ├── user.py             # User and Profile schemas
    │   ├── posts.py            # Post schemas (PostCreate, PostUpdate, PostResponse)
    │   ├── post_likes.py       # PostLike schemas (PostLikeCreate, PostLikeResponse)
    │   └── post_comments.py    # PostComment schemas (PostCommentCreate, PostCommentUpdate, PostCommentResponse) (NEW)
    ├── services/               # Business logic and database operations
    │   ├── __init__.py
    │   ├── auth.py             # Authentication service logic
    │   ├── user.py             # User service logic
    │   ├── posts.py            # Post service logic
    │   ├── post_likes.py       # PostLike service logic
    │   └── post_comments.py    # PostComment service logic (NEW)
    ├── controllers/            # Orchestrates requests between routers and services
    │   ├── __init__.py
    │   ├── auth.py             # Auth controller functions
    │   ├── user.py             # User controller functions
    │   ├── posts.py            # Post controller functions
    │   ├── post_likes.py       # PostLike controller functions
    │   └── post_comments.py    # PostComment controller functions (NEW)
    ├── routers/                # API endpoint definitions (FastAPI APIRouters)
    │   ├── __init__.py
    │   ├── auth.py             # Authentication routes
    │   ├── users.py            # User routes
    │   ├── posts.py            # Post routes
    │   ├── post_likes.py       # PostLike routes
    │   └── post_comments.py    # PostComment routes (NEW)
    ├── tests/                  # Automated tests for server functionality
    │   ├── __init__.py
    │   └── test_auth.py        # Tests for authentication (registration, login)
    ├── uploads/                # Directory for uploaded media files (e.g., post images/videos)
    │   └── .gitkeep            # Placeholder to keep directory in git
    └── utils/                  # Utility functions and cross-cutting concerns
        ├── __init__.py
        ├── app_setup.py        # App startup/shutdown, middleware, logging, global settings
        ├── db.py               # Database connection/session management
        ├── file_manager.py     # Local file system operations (save/delete uploads)
        └── security.py         # Password hashing, JWT handling, authentication dependencies

7. Best Practices & Design Principles
The Tea & Hive Backend API is built with a strong emphasis on modern software development best practices:

Layered Architecture (Separation of Concerns): Each component (model, schema, service, controller, router, utility) has a single, well-defined responsibility. This enhances modularity, maintainability, and testability.

Modularity: Features are implemented in dedicated files and directories, making the codebase easy to navigate and understand.

Dependency Injection: Database sessions (db: Session = Depends(get_db)) and authenticated user objects (current_user: User = Depends(get_current_user)) are injected, promoting loose coupling and testability.

Pydantic for Data Integrity: Extensive use of Pydantic models ensures robust data validation for incoming requests and consistent serialization for outgoing responses. from_attributes=True enables seamless mapping from SQLAlchemy ORM objects.

SQLAlchemy ORM: Utilizes SQLAlchemy for object-relational mapping, abstracting database interactions and leveraging its powerful features like relationship(), joinedload() for N+1 problem prevention, and UniqueConstraint for data integrity.

Database Query Optimization: Aggregations (e.g., likes_count, comments_count) and conditional checks (is_liked_by_current_user) are performed efficiently at the database level using SQLAlchemy's select, func.count(), subqueries, and CTEs, minimizing Python-side processing and data transfer.

Asynchronous Programming: FastAPI's async/await is used for I/O-bound operations (like database calls and file uploads), ensuring non-blocking performance.

Robust Error Handling:

Global exception handlers catch RequestValidationError, HTTPException, and generic Exception, providing consistent and informative JSON error responses to clients.

Specific business logic errors (e.g., "Post not found," "Already liked") are mapped to appropriate HTTP status codes (e.g., 404, 409).

Transactional Integrity: Database operations are wrapped in try...except blocks with db.rollback() to ensure atomicity and prevent data corruption. Orphaned file cleanup is integrated into the service layer.

Authentication & Authorization: Secure JWT-based authentication is implemented, with clear distinctions between required and optional authentication for different endpoints.

Configuration Management: All configurable parameters are externalized into .env files, allowing easy deployment across different environments without code changes.

Logging: Centralized and configurable logging provides clear insights into application behavior, aiding debugging and monitoring.

8. Testing
(Placeholder for future testing instructions)

Currently, testing involves manual verification via Swagger UI or Postman. As the project grows, comprehensive unit and integration tests will be implemented.

9. Contributing
(Placeholder for contribution guidelines)

Contributions are welcome! If you'd like to contribute, please follow these steps:

Fork the repository.

Create a new branch for your feature or bug fix.

Implement your changes following the existing code style and best practices.

Write tests for your changes.

Submit a pull request.

10. License
No License yet shh… 🤫

11. Contact
For any questions or inquiries, please contact:

Hive Team: Mohamed Ben Naima - Hachem Omri - Ghassen Chahdoura

Email: medbennaima2021@gmail.com

GitHub: Meeeeedd (Mohamed Ben Naima)