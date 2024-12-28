import os
import logging
from flask import Flask
from flask_talisman import Talisman
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Create Flask flask_app
talisman = Talisman()


def create_app():
    app = Flask(__name__)

    # Secret key for session and CSRF protection
    app.secret_key = os.getenv("APP_SECRET_KEY")

    # Configure upload settings
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max file size
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Configure Flask-Talisman for security headers
    csp = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "https://cdn.jsdelivr.net", "https://kit.fontawesome.com"],
        "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'", "https://kit.fontawesome.com", "https://cdn.jsdelivr.net"],
    }
    talisman.init_app(app, content_security_policy=csp)

    # Register blueprints
    from flask_app.routes import main
    app.register_blueprint(main)

    # Inject current year into templates
    @app.context_processor
    def inject_year():
        return {"year": datetime.now().year}

    return app
