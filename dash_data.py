"""Aggregate metrics for admin / doctor / patient dashboards — DB-backed."""
from __future__ import annotations

import datetime as dt
from typing import Any

from diagnosis_logic import human_label_test_type
from models import (
    Appointment,
    BloodDonor,
    BloodInventory,
    DiagnosisReport,
    DonorSupply,
    Feedback,
    MedicalReport,
    Notification,
    PredictionLog,
    db,
)
from models.user import User

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


def _today_date() -> dt.date:
    return dt.date.today()


def _week_labels_and_buckets(day_count: int) -> tuple[list[str], dict[dt.date, int]]:
    today = _today_date()
    labels: list[str] = []
    buckets: dict[dt.date, int] = {}
    for i in range(day_count - 1, -1, -1):
        d = today - dt.timedelta(days=i)
        labels.append(d.strftime("%d %b"))
        buckets[d] = 0
    return labels, buckets


def _ensure_blood_inventory_rows() -> None:
    existing = {row.blood_group for row in BloodInventory.query.all()}
    created = False
    for group in BLOOD_GROUPS:
        if group not in existing:
            db.session.add(BloodInventory(blood_group=group, units_available=0, last_updated=dt.datetime.utcnow()))
            created = True
    if created:
        db.session.commit()


def admin_dashboard_payload() -> dict[str, Any]:
    today = _today_date()
    _ensure_blood_inventory_rows()

    total_patients = User.query.filter_by(role="patient").count()
    total_doctors = User.query.filter_by(role="doctor").count()

    appointments_today = Appointment.query.filter(
        Appointment.appointment_date == today,
        Appointment.status != "cancelled",
    ).count()

    critical_open = Appointment.query.filter(
        Appointment.emergency.is_(True),
        Appointment.status == "scheduled",
    ).count()

    blood_rows = BloodInventory.query.order_by(BloodInventory.blood_group).all()
    if not blood_rows:
        # Backward compatible fallback for existing donor_supply table.
        blood_rows = DonorSupply.query.order_by(DonorSupply.blood_group).all()
    donor_units = sum(int(r.units_available) for r in blood_rows)
    total_blood_donors = BloodDonor.query.count()
    low_stock_alerts = [r for r in blood_rows if int(r.units_available) < 5]

    labels_appt, buckets_appt = _week_labels_and_buckets(7)
    week_floor = today - dt.timedelta(days=6)
    for a in Appointment.query.filter(Appointment.appointment_date >= week_floor).all():
        buckets_appt[a.appointment_date] = buckets_appt.get(a.appointment_date, 0) + 1
    chart_appt_values = [buckets_appt.get(today - dt.timedelta(days=i), 0) for i in range(6, -1, -1)]

    labels_pred, buckets_pred = _week_labels_and_buckets(14)
    pred_floor = dt.datetime.combine(today - dt.timedelta(days=13), dt.time.min)
    for p in PredictionLog.query.filter(PredictionLog.created_at >= pred_floor).all():
        dk = p.created_at.date()
        buckets_pred[dk] = buckets_pred.get(dk, 0) + 1
    chart_prediction_values = [buckets_pred.get(today - dt.timedelta(days=i), 0) for i in range(13, -1, -1)]

    conf_rows = (
        PredictionLog.query.with_entities(PredictionLog.confidence)
        .filter(PredictionLog.confidence.isnot(None))
        .all()
    )
    conf_vals = [float(c[0]) for c in conf_rows if c[0] is not None]
    avg_prediction_confidence = round(sum(conf_vals) / len(conf_vals), 3) if conf_vals else None

    week_prediction_volume = PredictionLog.query.filter(PredictionLog.created_at >= pred_floor).count()

    charts = {
        "appt_line": {"labels": labels_appt, "values": chart_appt_values},
        "pred_line": {"labels": labels_pred, "values": chart_prediction_values},
    }

    diag_q = (
        db.session.query(DiagnosisReport, User.name)
        .join(User, DiagnosisReport.patient_id == User.id)
        .order_by(DiagnosisReport.created_at.desc())
        .limit(50)
        .all()
    )
    diagnosis_dashboard_rows = [
        {"rep": r, "patient_name": pname, "type_label": human_label_test_type(r.test_type)}
        for r, pname in diag_q
    ]

    inbox_q = (
        db.session.query(Notification, User.name, User.role)
        .join(User, Notification.user_id == User.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
        .all()
    )
    admin_notification_rows = [
        {"n": n_row, "recipient_name": rcpt_name, "recipient_role": rcpt_role}
        for n_row, rcpt_name, rcpt_role in inbox_q
    ]
    feedback_rows = Feedback.query.order_by(Feedback.created_at.desc()).limit(200).all()

    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "appointments_today": appointments_today,
        "critical_cases": critical_open,
        "donor_units_total": donor_units,
        "total_blood_donors": total_blood_donors,
        "donor_supply_rows": blood_rows,
        "low_stock_alert_rows": low_stock_alerts,
        "chart_appt_labels": labels_appt,
        "chart_appt_values": chart_appt_values,
        "chart_prediction_labels": labels_pred,
        "chart_prediction_values": chart_prediction_values,
        "avg_prediction_confidence": avg_prediction_confidence,
        "predictions_week_count": week_prediction_volume,
        "charts": charts,
        "diagnosis_dashboard_rows": diagnosis_dashboard_rows,
        "admin_notification_rows": admin_notification_rows,
        "feedback_rows": feedback_rows,
    }


def doctor_dashboard_payload(doctor_id: int) -> dict[str, Any]:
    today = _today_date()
    _ensure_blood_inventory_rows()
    week_floor_date = today - dt.timedelta(days=6)

    todays_appts_q = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == today,
        Appointment.status != "cancelled",
    ).all()
    # Sort by composite slot time ascending for timeline; priority list separate
    todays_sorted = sorted(todays_appts_q, key=lambda a: a.slot_datetime())

    priority_queue_q = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "scheduled",
        Appointment.appointment_date >= today - dt.timedelta(days=7),
    ).all()

    emergency_alerts_q = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.emergency.is_(True),
        Appointment.appointment_date >= today - dt.timedelta(days=3),
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).limit(8).all()

    history_q = (
        Appointment.query.filter(Appointment.doctor_id == doctor_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .limit(10)
        .all()
    )
    history_rows = []
    for a in history_q:
        patient = db.session.get(User, a.patient_id)
        history_rows.append(
            {
                "when": a.slot_datetime(),
                "patient_name": patient.name if patient else f"#{a.patient_id}",
                "title": (a.symptoms or "")[:80] or a.department,
                "status": a.status,
            }
        )

    labels, buckets = _week_labels_and_buckets(7)
    for a in Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date >= week_floor_date,
    ).all():
        buckets[a.appointment_date] = buckets.get(a.appointment_date, 0) + 1
    schedule_chart_values = [buckets.get(today - dt.timedelta(days=i), 0) for i in range(6, -1, -1)]

    def row(a: Appointment) -> dict[str, Any]:
        p = db.session.get(User, a.patient_id)
        return {"a": a, "patient_name": p.name if p else f"#{a.patient_id}"}

    upcoming_future = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date > today,
            Appointment.status != "cancelled",
        )
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
        .limit(80)
        .all()
    )

    charts = {"schedule_line": {"labels": labels, "values": schedule_chart_values}}

    patient_scope = (
        db.session.query(Appointment.patient_id)
        .filter(Appointment.doctor_id == doctor_id)
        .distinct()
        .all()
    )
    patient_ids_doc = [p[0] for p in patient_scope]
    diagnosis_doctor_rows: list[dict[str, Any]] = []
    if patient_ids_doc:
        diag_joint = (
            db.session.query(DiagnosisReport, User.name)
            .join(User, DiagnosisReport.patient_id == User.id)
            .filter(DiagnosisReport.patient_id.in_(patient_ids_doc))
            .order_by(DiagnosisReport.created_at.desc())
            .limit(40)
            .all()
        )
        diagnosis_doctor_rows = [
            {"rep": r, "patient_name": pname, "type_label": human_label_test_type(r.test_type)}
            for r, pname in diag_joint
        ]

    return {
        "todays_appts": [row(a) for a in todays_sorted],
        "upcoming_future_appts": [row(a) for a in upcoming_future],
        "priority_queue": [row(a) for a in sorted(priority_queue_q, key=lambda x: (-x.priority_score, x.slot_datetime()))],
        "emergency_alerts": [row(a) for a in emergency_alerts_q],
        "patient_history": history_rows,
        "schedule_chart_labels": labels,
        "schedule_chart_values": schedule_chart_values,
        "charts": charts,
        "diagnosis_doctor_rows": diagnosis_doctor_rows,
        "blood_inventory_rows": BloodInventory.query.order_by(BloodInventory.blood_group.asc()).all(),
    }


def patient_dashboard_payload(patient_id: int) -> dict[str, Any]:
    now = dt.datetime.now()
    today = _today_date()

    candidates = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.status != "cancelled",
    ).all()
    upcoming_sorted = sorted(
        [a for a in candidates if a.slot_datetime() >= now],
        key=lambda a: a.slot_datetime(),
    )[:12]

    reports = (
        MedicalReport.query.filter_by(patient_id=patient_id).order_by(MedicalReport.reported_at.desc()).limit(8).all()
    )

    notifications = (
        Notification.query.filter_by(user_id=patient_id).order_by(Notification.created_at.desc()).limit(12).all()
    )

    labels, buckets = _week_labels_and_buckets(7)
    week_floor_date = today - dt.timedelta(days=6)
    for a in Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.appointment_date >= week_floor_date,
    ).all():
        buckets[a.appointment_date] = buckets.get(a.appointment_date, 0) + 1
    care_values = [buckets.get(today - dt.timedelta(days=i), 0) for i in range(6, -1, -1)]

    unread = Notification.query.filter_by(user_id=patient_id, is_read=False).count()

    def up_row(a: Appointment) -> dict[str, Any]:
        d = db.session.get(User, a.doctor_id) if a.doctor_id else None
        return {"a": a, "doctor_name": d.name if d else "To be assigned"}

    upcoming_view = [up_row(a) for a in upcoming_sorted]

    charts = {"care_line": {"labels": labels, "values": care_values}}

    diagnosis_own = (
        DiagnosisReport.query.filter_by(patient_id=patient_id)
        .order_by(DiagnosisReport.created_at.desc())
        .limit(24)
        .all()
    )
    diagnosis_own_view = [{"rep": r, "type_label": human_label_test_type(r.test_type)} for r in diagnosis_own]

    return {
        "upcoming": upcoming_view,
        "reports": reports,
        "notifications": notifications,
        "care_labels": labels,
        "care_values": care_values,
        "unread_notifications": unread,
        "charts": charts,
        "diagnosis_reports": diagnosis_own_view,
    }


def db_scalar_sum_donors() -> int:
    rows = DonorSupply.query.all()
    return sum(r.units_available for r in rows)
