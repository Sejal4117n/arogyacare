"""In-app inbox: booking notices plus any future rows keyed by recipient user_id."""

from __future__ import annotations

import datetime as dt

from models import Notification, db

# Booking rows use these categories so filters / analytics can pivot if needed.
APPOINTMENT_CATEGORY = "appointment"
APPOINTMENT_EMERGENCY_CATEGORY = "appointment_emergency"


def format_ampm(appt_time: dt.time) -> str:
    h = appt_time.hour % 12 or 12
    m = appt_time.minute
    suffix = "AM" if appt_time.hour < 12 else "PM"
    return f"{h}:{m:02d} {suffix}"


def booking_day_words(appt_date: dt.date) -> str:
    today = dt.date.today()
    if appt_date == today:
        return "today"
    if appt_date == today + dt.timedelta(days=1):
        return "tomorrow"
    return appt_date.strftime("%d %b %Y")


def build_booking_notice(
    *,
    emergency: bool,
    patient_name: str,
    department: str,
    appt_date: dt.date,
    appt_time: dt.time,
    symptoms: str,
) -> tuple[str, str, str]:
    """Return (title, message, category) for `notifications`; message is stored in the `body` column."""
    time_label = format_ampm(appt_time)
    day_w = booking_day_words(appt_date)
    dept = (department or "").strip()
    lines = [
        f"Patient booked appointment {day_w} at {time_label}.",
        f"Patient: {patient_name}",
    ]
    if dept:
        lines.append(f"Department: {dept}")
    tail = symptoms.strip()
    if tail:
        snip = tail[:200] + ("…" if len(tail) > 200 else "")
        lines.append(f"Notes: {snip}")
    msg = "\n".join(lines)
    if emergency:
        msg += "\n\nEMERGENCY CASE"
    cat = APPOINTMENT_EMERGENCY_CATEGORY if emergency else APPOINTMENT_CATEGORY
    return "New Appointment", msg[:512], cat


def _is_emergency_notice(row: Notification) -> bool:
    if row.category == APPOINTMENT_EMERGENCY_CATEGORY:
        return True
    body = row.body or ""
    return "EMERGENCY CASE" in body.upper()


def serialize_notification(row: Notification) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "body": row.body,
        "message": row.body,
        "emergency": _is_emergency_notice(row),
        "read": row.is_read,
        "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
    }


def poll_for_doctor(doctor_id: int, limit: int = 25) -> dict:
    unread = Notification.query.filter(
        Notification.user_id == doctor_id,
        Notification.is_read.is_(False),
    ).count()
    rows = (
        Notification.query.filter(Notification.user_id == doctor_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"unread_count": unread, "items": [serialize_notification(r) for r in rows]}


def mark_notifications_read(user_id: int, ids: list[int] | None, mark_all_unread: bool) -> int:
    q = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.is_read.is_(False),
    )
    if not mark_all_unread:
        if not ids:
            return 0
        q = q.filter(Notification.id.in_(ids))

    rows = q.all()
    for row in rows:
        row.is_read = True
    if rows:
        db.session.commit()
    return len(rows)


