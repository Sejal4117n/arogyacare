"""Operational data for dashboards (appointments, reports, predictions, donors)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import synonym

from . import db


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    department = db.Column(db.String(120), nullable=False, index=True)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False)
    symptoms = db.Column(db.Text, nullable=False, default="")
    emergency = db.Column(db.Boolean, nullable=False, default=False)
    priority_score = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(32), nullable=False, default="scheduled")
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    def slot_datetime(self) -> dt.datetime:
        return dt.datetime.combine(self.appointment_date, self.appointment_time)


class MedicalReport(db.Model):
    __tablename__ = "medical_reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(240), nullable=False)
    report_type = db.Column(db.String(80), nullable=False, default="laboratory")
    file_path = db.Column(db.String(512), nullable=True)
    reported_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True)


class PredictionLog(db.Model):
    __tablename__ = "prediction_logs"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    headline = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(80), nullable=False, default="general")
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.String(512), nullable=False)
    message = synonym("body")
    category = db.Column(db.String(64), nullable=False, default="care")
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True)


class DonorSupply(db.Model):
    __tablename__ = "donor_supply"

    id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(8), nullable=False, unique=True)
    units_available = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)


class DiagnosisReport(db.Model):
    __tablename__ = "diagnosis_reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    test_type = db.Column(db.String(64), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    result = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True)


class BloodInventory(db.Model):
    __tablename__ = "blood_inventory"

    id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(8), nullable=False, unique=True, index=True)
    units_available = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True)


class BloodDonor(db.Model):
    __tablename__ = "blood_donors"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    donor_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(8), nullable=False, index=True)
    phone = db.Column(db.String(32), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    donated_on = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True)
    status = db.Column(db.String(20), nullable=False, default="Eligible", index=True)


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True)
