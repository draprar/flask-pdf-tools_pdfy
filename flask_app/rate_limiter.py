"""
Rate limiting middleware for Flask PDF Tools.

Prevents abuse by limiting:
- File upload requests (max 5 per minute per IP)
- CAPTCHA validation attempts (max 10 per minute per IP)
- Download requests (max 20 per minute per IP)
"""

import time
from collections import defaultdict
from functools import wraps
from flask import request, flash, redirect, url_for


class RateLimiter:
    """
    Simple in-memory rate limiter based on IP address.

    Production note: For distributed systems, use Redis-based rate limiting.
    This implementation is suitable for single-server deployments.
    """

    def __init__(self):
        """Initialize rate limiter with empty tracking."""
        # Format: {endpoint: {ip: [(timestamp, count), ...]}}
        self._requests = defaultdict(lambda: defaultdict(list))

    def is_limited(self, ip, endpoint, max_requests=5, window_seconds=60):
        """
        Check if IP has exceeded rate limit for endpoint.

        Args:
            ip (str): Client IP address
            endpoint (str): Endpoint identifier (e.g., 'join_pdfs')
            max_requests (int): Maximum requests allowed in window
            window_seconds (int): Time window in seconds

        Returns:
            bool: True if rate limited (request should be rejected)
        """
        now = time.time()
        window_start = now - window_seconds

        # Get request history for this IP/endpoint
        requests = self._requests[endpoint][ip]

        # Remove old requests outside the window
        requests[:] = [(ts, count) for ts, count in requests if ts > window_start]

        # Check if limit exceeded
        total_requests = sum(count for _, count in requests)

        if total_requests >= max_requests:
            return True

        # Record this request
        if requests and requests[-1][0] == now:
            # Same timestamp, increment count
            requests[-1] = (now, requests[-1][1] + 1)
        else:
            # New timestamp
            requests.append((now, 1))

        return False

    def get_remaining(self, ip, endpoint, max_requests=5, window_seconds=60):
        """
        Get remaining requests for IP/endpoint.

        Args:
            ip (str): Client IP address
            endpoint (str): Endpoint identifier
            max_requests (int): Maximum requests allowed in window
            window_seconds (int): Time window in seconds

        Returns:
            int: Number of remaining requests in current window
        """
        now = time.time()
        window_start = now - window_seconds

        requests = self._requests[endpoint][ip]
        requests[:] = [(ts, count) for ts, count in requests if ts > window_start]

        total_requests = sum(count for _, count in requests)
        return max(0, max_requests - total_requests)

    def reset(self, ip=None, endpoint=None):
        """
        Reset rate limit counters.

        Args:
            ip (str, optional): Reset only this IP (all endpoints)
            endpoint (str, optional): Reset only this endpoint (all IPs)
        """
        if ip and endpoint:
            self._requests[endpoint][ip].clear()
        elif ip:
            for ep in self._requests:
                self._requests[ep][ip].clear()
        elif endpoint:
            self._requests[endpoint].clear()
        else:
            self._requests.clear()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(endpoint, max_requests=5, window_seconds=60):
    """
    Decorator to apply rate limiting to a Flask route.

    Args:
        endpoint (str): Endpoint identifier
        max_requests (int): Maximum requests allowed in window
        window_seconds (int): Time window in seconds

    Example:
        @app.route('/join', methods=['POST'])
        @rate_limit('join_pdfs', max_requests=10, window_seconds=60)
        def join_pdfs():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = get_client_ip()

            if _rate_limiter.is_limited(ip, endpoint, max_requests, window_seconds):
                flash(
                    f"Too many requests. Please wait before trying again.",
                    "error"
                )
                return redirect(url_for("main.home"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_client_ip():
    """
    Get client IP address, respecting proxy headers.

    Returns:
        str: Client IP address
    """
    # Check for IP behind reverse proxy
    if request.headers.get("X-Forwarded-For"):
        # X-Forwarded-For can contain multiple IPs, get the first
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()

    if request.headers.get("CF-Connecting-IP"):
        # Cloudflare
        return request.headers.get("CF-Connecting-IP")

    if request.headers.get("X-Real-IP"):
        # Nginx
        return request.headers.get("X-Real-IP")

    # Direct connection
    return request.remote_addr or "0.0.0.0"


def init_rate_limiting(app):
    """
    Initialize rate limiting configuration.

    Args:
        app: Flask application instance
    """
    # Store rate limiter in app for testing/management
    app.rate_limiter = _rate_limiter

    # Log initialization
    app.logger.info("Rate limiting initialized")


# Rate limit configuration (adjust based on your needs)
RATE_LIMITS = {
    "join_pdfs": {
        "max_requests": 10,
        "window_seconds": 300,  # 5 minutes
        "description": "Join/merge PDF files"
    },
    "split_pdf": {
        "max_requests": 10,
        "window_seconds": 300,  # 5 minutes
        "description": "Split PDF files"
    },
    "download_file": {
        "max_requests": 30,
        "window_seconds": 60,  # 1 minute
        "description": "Download files"
    },
}

