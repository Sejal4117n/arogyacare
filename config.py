"""Application configuration for ArogyaCare (Flask + MySQL / XAMPP)."""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (same directory as this file's parent)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


def _database_uri() -> str:
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "arogyacare")
    # XAMPP default is often empty password; URL-encode special chars in production
    if password:
        from urllib.parse import quote_plus

        password = quote_plus(password)
        auth = f"{user}:{password}"
    else:
        auth = user
    return f"mysql+pymysql://{auth}@{host}:{port}/{database}?charset=utf8mb4"


class Config:
    """Base configuration — override via environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
