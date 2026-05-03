"""Admin analytics payloads for dashboard cards/charts and Power BI APIs."""
from __future__ import annotations

import datetime as dt
from collections import Counter
from typing import Any

from sqlalchemy import func

from models import Appointment, BloodDonor, BloodInventory, DiagnosisReport, MedicalReport, Notification, db
from models.user import User

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


def _month_floor() -> dt.datetime:
    now = dt.datetime.now()
    return dt.datetime(now.year, now.month, 1, 0, 0, 0)


def _ensure_blood_inventory_rows() -> None:
    existing = {row.blood_group for row in BloodInventory.query.all()}
    added = False
    for group in BLOOD_GROUPS:
        if group not in existing:
            db.session.add(BloodInventory(blood_group=group, units_available=0, last_updated=dt.datetime.utcnow()))
            added = True
    if added:
        db.session.commit()


def _user_gender_breakdown() -> dict[str, int]:
    # Users table has no dedicated gender column; derive from donor profile when available.
    rows = (
        db.session.query(BloodDonor.patient_id, BloodDonor.gender)
        .order_by(BloodDonor.patient_id.asc(), BloodDonor.donated_on.desc())
        .all()
    )
    latest: dict[int, str] = {}
    for patient_id, gender in rows:
        if patient_id not in latest:
            latest[patient_id] = (gender or "").strip().title()

    patient_ids = [u.id for u in User.query.filter_by(role="patient").all()]
    male = 0
    female = 0
    for pid in patient_ids:
        gender = latest.get(pid, "")
        if gender == "Male":
            male += 1
        elif gender == "Female":
            female += 1
    return {"male_patients": male, "female_patients": female, "unknown_patients": max(0, len(patient_ids) - male - female)}


def _new_patients_this_month() -> int:
    # Prefer created_at if schema has it; otherwise return 0 to avoid breaking existing DB.
    users_table = User.__table__
    if "created_at" not in users_table.c:
        return 0
    floor = _month_floor()
    return User.query.filter(User.role == "patient", users_table.c.created_at >= floor).count()


def patient_analytics() -> dict[str, Any]:
    total_patients = User.query.filter_by(role="patient").count()
    new_patients_this_month = _new_patients_this_month()
    gender = _user_gender_breakdown()

    age_bins = {"0-17": 0, "18-30": 0, "31-45": 0, "46-60": 0, "60+": 0, "Unknown": 0}
    today = dt.date.today()
    for u in User.query.filter_by(role="patient").all():
        if not u.date_of_birth:
            age_bins["Unknown"] += 1
            continue
        years = (today - u.date_of_birth).days // 365
        if years <= 17:
            age_bins["0-17"] += 1
        elif years <= 30:
            age_bins["18-30"] += 1
        elif years <= 45:
            age_bins["31-45"] += 1
        elif years <= 60:
            age_bins["46-60"] += 1
        else:
            age_bins["60+"] += 1

    return {
        "total_registered_patients": total_patients,
        "new_patients_this_month": new_patients_this_month,
        **gender,
        "age_group_analysis": age_bins,
    }


def doctor_analytics() -> dict[str, Any]:
    total_doctors = User.query.filter_by(role="doctor").count()
    dept_rows = (
        db.session.query(User.department, func.count(User.id))
        .filter(User.role == "doctor")
        .group_by(User.department)
        .all()
    )
    department_wise = [
        {"department": (dept or "Not Set"), "doctor_count": int(count)} for dept, count in dept_rows
    ]

    workload_rows = (
        db.session.query(User.id, User.name, func.count(Appointment.id))
        .join(Appointment, Appointment.doctor_id == User.id)
        .filter(User.role == "doctor")
        .group_by(User.id, User.name)
        .all()
    )
    doctor_workload = [
        {"doctor_id": int(did), "doctor_name": name, "appointment_count": int(cnt)} for did, name, cnt in workload_rows
    ]
    return {
        "total_doctors": total_doctors,
        "department_wise_doctors": department_wise,
        "doctor_workload": doctor_workload,
    }


def appointment_analytics() -> dict[str, Any]:
    today = dt.date.today()
    now = dt.datetime.now()
    total = Appointment.query.count()
    today_count = Appointment.query.filter(Appointment.appointment_date == today).count()
    upcoming = Appointment.query.filter(
        Appointment.status != "cancelled",
        Appointment.appointment_date >= today,
    ).count()
    completed = Appointment.query.filter(Appointment.status == "completed").count()
    cancelled = Appointment.query.filter(Appointment.status == "cancelled").count()
    dept_rows = (
        db.session.query(Appointment.department, func.count(Appointment.id))
        .group_by(Appointment.department)
        .all()
    )
    department_wise = [{"department": d, "appointments": int(c)} for d, c in dept_rows]
    peak = (
        db.session.query(Appointment.appointment_time, func.count(Appointment.id))
        .group_by(Appointment.appointment_time)
        .order_by(func.count(Appointment.id).desc())
        .first()
    )
    peak_label = peak[0].strftime("%H:%M") if peak and peak[0] else "N/A"
    month_floor = dt.datetime(now.year, now.month, 1)
    return {
        "total_appointments": total,
        "todays_appointments": today_count,
        "upcoming_appointments": upcoming,
        "completed_appointments": completed,
        "cancelled_appointments": cancelled,
        "department_wise_appointments": department_wise,
        "peak_booking_time": peak_label,
        "new_appointments_this_month": Appointment.query.filter(Appointment.created_at >= month_floor).count(),
    }


def diagnosis_analytics() -> dict[str, Any]:
    heart_count = DiagnosisReport.query.filter(DiagnosisReport.test_type == "heart").count()
    diabetes_count = DiagnosisReport.query.filter(DiagnosisReport.test_type == "diabetes").count()
    rows = DiagnosisReport.query.with_entities(DiagnosisReport.result).all()
    labels = Counter()
    for (res,) in rows:
        r = (res or "").lower()
        if "low risk" in r:
            labels["low_risk"] += 1
        elif "medium risk" in r:
            labels["medium_risk"] += 1
        elif "high risk" in r:
            labels["high_risk"] += 1
    return {
        "heart_prediction_count": heart_count,
        "diabetes_prediction_count": diabetes_count,
        "low_risk": labels["low_risk"],
        "medium_risk": labels["medium_risk"],
        "high_risk": labels["high_risk"],
    }


def blood_bank_analytics() -> dict[str, Any]:
    _ensure_blood_inventory_rows()
    total_donors = BloodDonor.query.count()
    stock_rows = BloodInventory.query.order_by(BloodInventory.blood_group.asc()).all()
    blood_group_wise_stock = [
        {"blood_group": r.blood_group, "units_available": int(r.units_available)} for r in stock_rows
    ]
    month_floor = _month_floor()
    monthly_donations = BloodDonor.query.filter(BloodDonor.donated_on >= month_floor).count()
    low_stock_alerts = [
        {"blood_group": r.blood_group, "units_available": int(r.units_available), "alert": "Low stock"}
        for r in stock_rows
        if int(r.units_available) < 5
    ]
    return {
        "total_donors": total_donors,
        "blood_group_wise_stock": blood_group_wise_stock,
        "monthly_donations": monthly_donations,
        "low_stock_alerts": low_stock_alerts,
    }


def notification_analytics() -> dict[str, Any]:
    return {"total_notifications_sent": Notification.query.count()}


def report_analytics() -> dict[str, Any]:
    return {"total_medical_reports": MedicalReport.query.count()}


def all_power_bi_payload() -> dict[str, Any]:
    return {
        "patient_analytics": patient_analytics(),
        "doctor_analytics": doctor_analytics(),
        "appointment_analytics": appointment_analytics(),
        "diagnosis_analytics": diagnosis_analytics(),
        "blood_bank_analytics": blood_bank_analytics(),
        "notification_analytics": notification_analytics(),
        "report_analytics": report_analytics(),
    }
