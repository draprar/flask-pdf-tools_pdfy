import os
import secrets
import logging
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for the application."""
    _secret_key = os.getenv("APP_SECRET_KEY")
    
    if not _secret_key:
        _secret_key = secrets.token_hex(32)
        if os.getenv("FLASK_ENV") == "production":
            logging.warning(
                "APP_SECRET_KEY not set in production! Using generated secret. "
                "Set APP_SECRET_KEY environment variable for consistency."
            )
    
    SECRET_KEY = _secret_key
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10)) * 1024 * 1024
    TALISMAN_FORCE_HTTPS = os.getenv("FLASK_ENV") == "production"
    TALISMAN_CSP = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "https://cdn.jsdelivr.net", "https://kit.fontawesome.com"],
        "style-src": ["'self'", "https://cdn.jsdelivr.net"],  # Removed unsafe-inline
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'", "https://kit.fontawesome.com", "https://cdn.jsdelivr.net"],
    }


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
