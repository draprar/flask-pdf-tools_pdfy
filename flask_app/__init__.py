import os
import logging
import base64
from flask import Flask
from flask_talisman import Talisman

talisman = Talisman()


def b64encode(value):
    """Base64 encode a value for use in templates."""
    return base64.b64encode(value).decode('utf-8')


def create_app():
    app = Flask(__name__)
    app.config.from_object("flask_app.config.Config")

    # Create upload folder if it doesn't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize Talisman for security headers
    is_production = os.getenv("FLASK_ENV") == "production"
    talisman.init_app(app,
                      content_security_policy=app.config["TALISMAN_CSP"],
                      force_https=is_production)

    # Register custom filters
    app.jinja_env.filters['b64encode'] = b64encode

    # Register blueprints
    from flask_app.routes import main
    app.register_blueprint(main)

    # Inject current year into templates
    @app.context_processor
    def inject_year():
        from datetime import datetime
        return {"year": datetime.now().year}

    return app
