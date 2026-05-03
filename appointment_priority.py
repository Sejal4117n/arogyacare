"""Priority score for appointments: P = E + A + B (emergency, age, earliness of slot)."""
from __future__ import annotations

from datetime import date


def patient_age_years(dob: date, ref: date | None = None) -> int | None:
    if dob is None:
        return None
    ref = ref or date.today()
    age = ref.year - dob.year
    if (ref.month, ref.day) < (dob.month, dob.day):
        age -= 1
    return age


def earliness_bonus(appointment_date: date, ref: date | None = None) -> int:
    """
    B: sooner calendar date → higher bonus (today = 15, each day later loses 1, floor 1).
    """
    ref = ref or date.today()
    days_diff = (appointment_date - ref).days
    if days_diff < 0:
        return 1
    return max(1, 15 - min(days_diff, 14))


def compute_priority_score(
    *,
    emergency: bool,
    patient_dob: date | None,
    appointment_date: date,
) -> int:
    E = 10 if emergency else 0
    age = patient_age_years(patient_dob)
    A = 5 if age is not None and age > 60 else 0
    B = earliness_bonus(appointment_date)
    return E + A + B
