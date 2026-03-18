"""
Logging configuration for Flask PDF Tools.

This module provides production-ready logging setup with:
- Console and file output
- Log rotation
- Multiple log levels
- Structured logging format
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(app):
    """
    Configure application logging with file and console handlers.

    Args:
        app: Flask application instance

    Features:
        - Console handler for immediate feedback
        - File handler with rotation (10MB, 5 backups)
        - Environment-specific log levels
        - Structured log format with timestamp, module, level
        - Separate error log file for critical issues
    """
    # Determine log level based on environment
    log_level = logging.DEBUG if os.getenv("FLASK_ENV") == "development" else logging.INFO

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Remove default handlers
    app.logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stderr for error logging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # Main application log file with rotation
    app_log_path = log_dir / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        str(app_log_path),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    # Error log file (errors and above)
    error_log_path = log_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        str(error_log_path),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    app.logger.addHandler(error_handler)

    # Security log file (security-related events)
    security_log_path = log_dir / "security.log"
    security_handler = logging.handlers.RotatingFileHandler(
        str(security_log_path),
        maxBytes=5 * 1024 * 1024,  # 5MB (smaller for security logs)
        backupCount=10,  # Keep more backups of security logs
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(formatter)

    # Create security logger
    security_logger = logging.getLogger("flask_app.security")
    security_logger.setLevel(logging.WARNING)
    security_logger.addHandler(security_handler)

    # Set app logger level
    app.logger.setLevel(log_level)

    # Log startup information
    app.logger.info(f"Logging configured - Level: {logging.getLevelName(log_level)}")
    app.logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    app.logger.info(f"Log directory: {log_dir.absolute()}")

    return app.logger, security_logger


def get_security_logger():
    """
    Get the security logger for logging security-related events.

    Returns:
        logging.Logger: Security logger instance
    """
    return logging.getLogger("flask_app.security")


def log_security_event(event_type, message, user_ip=None, extra_data=None):
    """
    Log a security event with structured information.

    Args:
        event_type (str): Type of security event (e.g., 'SUSPICIOUS', 'BLOCKED', 'FAILURE')
        message (str): Event message
        user_ip (str, optional): User's IP address
        extra_data (dict, optional): Additional context data
    """
    logger = get_security_logger()

    log_message = f"[{event_type}] {message}"
    if user_ip:
        log_message += f" | IP: {user_ip}"
    if extra_data:
        log_message += f" | Data: {extra_data}"

    logger.warning(log_message)

