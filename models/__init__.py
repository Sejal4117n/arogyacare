"""SQLAlchemy models and shared db instance."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User  # noqa: E402
from models.clinical import (  # noqa: E402
    Appointment,
    BloodDonor,
    BloodInventory,
    DiagnosisReport,
    DonorSupply,
    Feedback,
    MedicalReport,
    Notification,
    PredictionLog,
)

__all__ = [
    "db",
    "User",
    "Appointment",
    "BloodInventory",
    "BloodDonor",
    "MedicalReport",
    "PredictionLog",
    "Notification",
    "DonorSupply",
    "DiagnosisReport",
    "Feedback",
]
