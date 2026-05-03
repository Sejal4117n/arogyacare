"""
ArogyaCare — Flask application entry point.
"""
from __future__ import annotations

import os
from typing import Optional

from flask import Blueprint, Flask, jsonify, redirect, render_template, request, url_for

from analytics_data import (
    all_power_bi_payload,
    appointment_analytics,
    blood_bank_analytics,
    diagnosis_analytics,
    doctor_analytics,
    notification_analytics,
    patient_analytics,
    report_analytics,
)
from auth import auth_bp, current_user, role_required
from blood_bank_views import init_blood_bank_views
from doctor_notifications import mark_notifications_read, poll_for_doctor
from booking_views import admin_appointments_full_rows, doctor_today_schedule_rows, init_booking_views
from config import config_by_name
from dash_data import admin_dashboard_payload, doctor_dashboard_payload, patient_dashboard_payload
from diagnosis_views import init_diagnosis
from models import Feedback, db


admin_bp = Blueprint("admin", __name__)
doctor_bp = Blueprint("doctor", __name__)
patient_bp = Blueprint("patient", __name__)


@admin_bp.route("/appointments")
@role_required("admin")
def admin_appointments_board():
    rows = admin_appointments_full_rows()
    return render_template("admin/appointments.html", rows=rows)


@admin_bp.route("/dashboard")
@role_required("admin")
def admin_dashboard():
    payload = admin_dashboard_payload()
    return render_template("admin/dashboard.html", **payload)


@admin_bp.route("/feedback")
@role_required("admin")
def admin_feedback_page():
    rows = Feedback.query.order_by(
        Feedback.created_at.desc()
    ).all()
    return render_template(
        "admin/feedback.html",
        rows=rows,
    )


@admin_bp.route("/")
def admin_home():
    return redirect(
        url_for("admin.admin_dashboard")
    )


@doctor_bp.route("/dashboard")
@role_required("doctor")
def doctor_dashboard():
    me = current_user()
    payload = doctor_dashboard_payload(
        me.id if me else -1
    )
    return render_template(
        "doctor/dashboard.html",
        **payload,
    )


@doctor_bp.route("/")
def doctor_home():
    return redirect(
        url_for("doctor.doctor_dashboard")
    )


@patient_bp.route("/dashboard")
@role_required("patient")
def patient_dashboard():
    me = current_user()
    payload = patient_dashboard_payload(
        me.id if me else -1
    )
    return render_template(
        "patient/dashboard.html",
        **payload,
    )


@patient_bp.route("/")
def patient_home():
    return redirect(
        url_for("patient.patient_dashboard")
    )


def create_app(
    config_name: Optional[str] = None
) -> Flask:

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    cfg = config_name or os.getenv(
        "FLASK_ENV",
        "development",
    )

    if cfg == "production":
        app.config.from_object(
            config_by_name["production"]
        )
    elif cfg == "testing":
        app.config.from_object(
            config_by_name["testing"]
        )
    else:
        app.config.from_object(
            config_by_name["development"]
        )

    db.init_app(app)

    # IMPORTANT FOR RENDER
    with app.app_context():
        db.create_all()

    init_booking_views(app)
    init_blood_bank_views(app)
    init_diagnosis(app)

    @app.route("/")
    def index():
        return render_template(
            "index.html"
        )

    @app.route(
        "/api/feedback",
        methods=["POST"],
    )
    def submit_feedback():

        payload = (
            request.get_json(
                silent=True
            ) or {}
        )

        name = (
            payload.get("name") or ""
        ).strip()

        message = (
            payload.get("message") or ""
        ).strip()

        try:
            rating = int(
                payload.get("rating")
            )
        except:
            rating = 0

        if (
            len(name) < 2
            or len(message) < 2
            or rating < 1
            or rating > 5
        ):
            return jsonify(
                {
                    "ok": False,
                    "error": "Invalid input",
                }
            ), 400

        row = Feedback(
            name=name,
            message=message,
            rating=rating,
        )

        db.session.add(row)
        db.session.commit()

        return jsonify(
            {
                "ok": True,
                "message": "Feedback submitted successfully",
            }
        )

    app.register_blueprint(auth_bp)
    app.register_blueprint(
        admin_bp,
        url_prefix="/admin",
    )
    app.register_blueprint(
        doctor_bp,
        url_prefix="/doctor",
    )
    app.register_blueprint(
        patient_bp,
        url_prefix="/patient",
    )

    @app.context_processor
    def inject_auth_nav():
        return {
            "current_auth_user": current_user()
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000",
            )
        ),
    )