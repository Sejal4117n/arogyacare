"""Clinical departments for booking and doctor assignment."""

from __future__ import annotations


DEPARTMENTS: tuple[str, ...] = (
    "General Medicine",
    "Cardiology",
    "Orthopedics",
    "Pediatrics",
    "Obstetrics & Gynecology",
    "Neurology",
    "Oncology",
    "Emergency Medicine",
    "Dermatology",
    "Psychiatry",
)


def normalize_department(val: str) -> str | None:
    """Return canonical department label or None."""
    if not val:
        return None
    cleaned = val.strip()
    for d in DEPARTMENTS:
        if d.lower() == cleaned.lower():
            return d
    return None
