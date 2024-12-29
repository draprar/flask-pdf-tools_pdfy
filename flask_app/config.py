import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("APP_SECRET_KEY", "default_secret_key")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10)) * 1024 * 1024
    TALISMAN_FORCE_HTTPS = os.getenv("FLASK_ENV") == "production"
    TALISMAN_CSP = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "https://cdn.jsdelivr.net", "https://kit.fontawesome.com"],
        "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'", "https://kit.fontawesome.com", "https://cdn.jsdelivr.net"],
    }