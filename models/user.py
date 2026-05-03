"""User model — MySQL `users` table."""
from __future__ import annotations

from . import db

VALID_ROLES = frozenset({"admin", "doctor", "patient"})


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    # Optional: clinical staff department; patients may set DOB for booking priority (age > 60)
    department = db.Column(db.String(120), nullable=True, index=True)
    date_of_birth = db.Column(db.Date, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
