"""
Seed admin + doctors for ArogyaCare.
Run:
python create_users.py
"""

from __future__ import annotations

import datetime as dt

from werkzeug.security import generate_password_hash

from app import app
from models import db, User


SEED_USERS = [

    # ADMIN
    {
        "name": "Sejal Chavan",
        "email": "sejal@arogyacare.com",
        "password": "admin123",
        "role": "admin",
        "department": "Administration",
        "date_of_birth": dt.date(2003, 9, 2),
    },
    {
        "name": "Abhishek Teregaon",
        "email": "abhishek@arogyacare.com",
        "password": "admin123",
        "role": "admin",
        "department": "Administration",
        "date_of_birth": dt.date(2003, 1, 1),
    },


    # DOCTORS
    {
        "name": "Dr Vishwanath Hesarur",
        "email": "hesarur@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Cardiology",
    },
    {
        "name": "Dr Sanjay Porwal",
        "email": "porwal@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Cardiology",
    },
    {
        "name": "Dr Meera Kulkarni",
        "email": "meera@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Pediatrics",
    },
    {
        "name": "Dr Shivakumar Patil",
        "email": "shivakumar@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Dermatology",
    },
    {
        "name": "Dr Sneha Deshpande",
        "email": "sneha@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Gynecology",
    },
    {
        "name": "Dr Raghavendra Patil",
        "email": "raghavendra@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Orthopedics",
    },
    {
        "name": "Dr Amit Joshi",
        "email": "amit@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Neurology",
    },
    {
        "name": "Dr Priti Hajare",
        "email": "priti@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "ENT",
    },
    {
        "name": "Dr Ankitha Narayan",
        "email": "ankitha@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "General Medicine",
    },
    {
        "name": "Dr Nikhil Desai",
        "email": "nikhil@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Urology",
    },
    {
        "name": "Dr Kavita Patankar",
        "email": "kavita@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Endocrinology",
    },
    {
        "name": "Dr Basavaraj Kajagar",
        "email": "kajagar@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "General Surgery",
    },
    {
        "name": "Dr Shruti Kulkarni",
        "email": "shruti@kle.com",
        "password": "doctor123",
        "role": "doctor",
        "department": "Ophthalmology",
    },
]


with app.app_context():

    for user_data in SEED_USERS:

        existing = User.query.filter_by(
            email=user_data["email"]
        ).first()

        if existing:
            print(f"Skipped: {user_data['email']} already exists")
            continue

        new_user = User(
            name=user_data["name"],
            email=user_data["email"],
            password=generate_password_hash(
                user_data["password"]
            ),
            role=user_data["role"],
            department=user_data.get("department"),
            date_of_birth=user_data.get("date_of_birth"),
        )

        db.session.add(new_user)

    db.session.commit()

    print("ArogyaCare users created successfully.")