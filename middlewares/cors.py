# Hive-server/middlewares/cors.py

from starlette.middleware.cors import CORSMiddleware
# Removed: from ..configs.settings import settings

def setup_cors_middleware(app, allow_origins: list[str], allow_methods: list[str], allow_headers: list[str]): # <-- NEW: Added parameters
    """
    Configures and adds CORS (Cross-Origin Resource Sharing) middleware to the FastAPI application.
    CORS settings are passed directly as arguments.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )