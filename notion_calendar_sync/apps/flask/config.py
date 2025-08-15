import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Flask configuration settings."""

    # General Config
    CALENDAR_FILE_PATH = os.environ.get("CALENDAR_FILE_PATH", "calendar.json")
    SECRET_KEY = os.environ.get("SECRET_KEY", "a-very-secret-key")
    FLASK_APP = os.environ.get("FLASK_APP", "app.py")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"

    # Server settings
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", 5000))

    # Security settings for production
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "True").lower() == "true"
    )
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_HTTPONLY = (
        os.environ.get("SESSION_COOKIE_HTTPONLY", "True").lower() == "true"
    )

    # Note on rate limiting:
    # For production, consider using a library like Flask-Limiter to protect against brute-force attacks.
    # Example: limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

    # Note on reverse proxy:
    # When deploying behind a reverse proxy like Tailscale's Caddy or Nginx,
    # ensure the proxy is configured to forward headers like X-Forwarded-For,
    # X-Forwarded-Proto, and X-Forwarded-Host. The application should be
    # configured to trust the proxy.
    # from werkzeug.middleware.proxy_fix import ProxyFix
    # app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
