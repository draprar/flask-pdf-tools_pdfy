import os
import logging
import base64
from datetime import datetime
from flask import Flask
from flask_talisman import Talisman

talisman = Talisman()


def b64encode(value):
    """Base64 encode a value for use in templates."""
    return base64.b64encode(value).decode("utf-8")


def create_app(config_name="default"):
    app = Flask(__name__)

    # Load configuration based on config_name
    if config_name == "testing":
        app.config.from_object("flask_app.config.TestingConfig")
    else:
        app.config.from_object("flask_app.config.Config")

    # Create upload folder if it doesn't exist
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create upload folder: {e}")
        raise

    # Configure logging (production-grade)
    if config_name != "testing":
        from flask_app.logging_config import setup_logging
        setup_logging(app)
    else:
        # Minimal logging for tests
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Initialize Talisman for security headers
    is_production = os.getenv("FLASK_ENV") == "production"
    talisman.init_app(
        app,
        content_security_policy=app.config["TALISMAN_CSP"],
        force_https=is_production,
        strict_transport_security=is_production,
        strict_transport_security_max_age=31536000 if is_production else None,
    )

    # Initialize rate limiting (abuse prevention)
    if config_name != "testing":
        from flask_app.rate_limiter import init_rate_limiting
        init_rate_limiting(app)

    # Register custom filters
    app.jinja_env.filters["b64encode"] = b64encode

    # Register blueprints
    from flask_app.routes import main
    app.register_blueprint(main)

    # Inject current year into templates
    @app.context_processor
    def inject_year():
        return {"year": datetime.now().year}

    return app
