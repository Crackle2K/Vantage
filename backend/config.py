"""
<<<<<<< Updated upstream
Centralised configuration — single source of truth for secrets and settings.

Every module that needs a secret should import it from here:

    from config import GOOGLE_API_KEY, MONGODB_URI

Values are loaded from backend/.env via python-dotenv.
=======
Vantage Configuration
Loads all secrets from .env — never hardcode or expose API keys.
>>>>>>> Stashed changes
"""

import os
from dotenv import load_dotenv

<<<<<<< Updated upstream
load_dotenv()  # reads .env in the same directory

MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME: str = os.getenv("DATABASE_NAME", "vantage")

SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

API_URL: str = os.getenv("API_URL", "http://localhost:8000")
=======
load_dotenv()

# ── MongoDB ─────────────────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "vantage")

# ── JWT / Auth ──────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

# ── Google Places API ───────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ── API ─────────────────────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://localhost:8000")
>>>>>>> Stashed changes
