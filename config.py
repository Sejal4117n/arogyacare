"""Application configuration for ArogyaCare."""
import os
from datetime import timedelta


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "arogyacare-secret-key",
    )

    # Render uses SQLite automatically if DATABASE_URL not set
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///arogyacare.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

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