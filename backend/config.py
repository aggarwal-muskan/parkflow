import os


class Config:
    # Flask secret key for sessions
    SECRET_KEY = "supersecret"
    DATABASE = "parking.db"

    REDIS_URL = "redis://localhost:6379/0"

    # For email — optional
    MAIL_SENDER = "noreply@parkingapp.com"

    # SQLite database path
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, "parking.db")
    SQLITE_URL = f"sqlite:///{DB_PATH}"

    # Redis (for caching & Celery)
    REDIS_URL = "redis://localhost:6379/0"


    # Celery configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # CORS (used in app.py via flask-cors)
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
