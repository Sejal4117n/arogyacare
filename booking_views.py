"""Patient booking, doctor roster API, wired inside create_app via init_booking_views."""
from __future__ import annotations

import datetime as dt

from flask import flash, jsonify, redirect, render_template, request, url_for

from appointment_priority import compute_priority_score
from auth import current_user, role_required
from departments import DEPARTMENTS, normalize_department
from doctor_notifications import build_booking_notice
from models import Appointment, Notification, db, User


def init_booking_views(app):
    @app.route("/book-appointment", methods=["GET", "POST"])
    @role_required("patient")
    def book_appointment():
        me = current_user()
        if me is None:
            return redirect(url_for("auth.login"))

        if request.method == "POST":
            department = normalize_department(request.form.get("department", ""))
            doctor_id_raw = request.form.get("doctor_id", "").strip()
            date_raw = request.form.get("appointment_date", "").strip()
            time_raw = request.form.get("appointment_time", "").strip()
            symptoms = (request.form.get("symptoms") or "").strip()
            emergency = request.form.get("emergency") == "on"

            errors = False
            if not department:
                flash("Select a department.", "danger")
                errors = True
            if not doctor_id_raw.isdigit():
                flash("Select a doctor.", "danger")
                errors = True
            if not date_raw or not time_raw:
                flash("Choose date and time.", "danger")
                errors = True
            if len(symptoms) < 3:
                flash("Describe symptoms in a few words (min 3 characters).", "danger")
                errors = True

            doctor_id = int(doctor_id_raw) if doctor_id_raw.isdigit() else 0
            doctor = db.session.get(User, doctor_id) if doctor_id else None
            if doctor is None or doctor.role != "doctor":
                flash("Invalid doctor selection.", "danger")
                errors = True
            elif department and normalize_department(doctor.department or "") != department:
                flash("Doctor does not match the selected department (or profile has no department).", "danger")
                errors = True

            appt_date = None
            appt_time = None
            try:
                appt_date = dt.datetime.strptime(date_raw, "%Y-%m-%d").date()
                appt_time = dt.datetime.strptime(time_raw, "%H:%M").time()
            except ValueError:
                flash("Invalid date or time format.", "danger")
                errors = True

            if appt_date and appt_time:
                slot = dt.datetime.combine(appt_date, appt_time)
                if slot < dt.datetime.now():
                    flash("Appointment must be in the future.", "danger")
                    errors = True

            if errors:
                return render_template(
                    "patient/book_appointment.html",
                    departments=DEPARTMENTS,
                    form_department=department or request.form.get("department", ""),
                    form_doctor_id=doctor_id_raw,
                    form_date=date_raw,
                    form_time=time_raw,
                    form_symptoms=symptoms,
                    form_emergency=emergency,
                )

            assert appt_date is not None and appt_time is not None and doctor is not None and department

            slot_busy = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == appt_date,
                Appointment.appointment_time == appt_time,
                Appointment.status != "cancelled",
            ).first()
            if slot_busy is not None:
                flash("This time slot is already booked. Please choose another.", "danger")
                return render_template(
                    "patient/book_appointment.html",
                    departments=DEPARTMENTS,
                    form_department=department or request.form.get("department", ""),
                    form_doctor_id=doctor_id_raw,
                    form_date=date_raw,
                    form_time=time_raw,
                    form_symptoms=symptoms,
                    form_emergency=emergency,
                )

            priority = compute_priority_score(
                emergency=emergency,
                patient_dob=me.date_of_birth,
                appointment_date=appt_date,
            )

            appt = Appointment(
                patient_id=me.id,
                doctor_id=doctor.id,
                department=department,
                appointment_date=appt_date,
                appointment_time=appt_time,
                symptoms=symptoms,
                emergency=emergency,
                priority_score=priority,
                status="scheduled",
            )
            n_title, n_message, n_cat = build_booking_notice(
                emergency=emergency,
                patient_name=me.name,
                department=department,
                appt_date=appt_date,
                appt_time=appt_time,
                symptoms=symptoms,
            )
            inbox = Notification(
                user_id=doctor.id,
                title=n_title,
                body=n_message,
                category=n_cat,
                is_read=False,
            )
            db.session.add(appt)
            db.session.add(inbox)
            db.session.commit()
            flash("Appointment booked successfully.", "success")
            return redirect(url_for("patient.patient_dashboard"))

        return render_template(
            "patient/book_appointment.html",
            departments=DEPARTMENTS,
            form_department="",
            form_doctor_id="",
            form_date="",
            form_time="",
            form_symptoms="",
            form_emergency=False,
        )

    @app.route("/api/doctors/by-department")
    @role_required("patient")
    def api_doctors_by_department():
        dept = normalize_department(request.args.get("department", ""))
        if not dept:
            return jsonify([])
        docs = User.query.filter_by(role="doctor", department=dept).order_by(User.name.asc()).all()
        return jsonify([{"id": d.id, "name": d.name} for d in docs])


def doctor_today_schedule_rows(doctor_id: int) -> list[dict]:
    today = dt.date.today()
    rows = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == today,
        Appointment.status != "cancelled",
    ).all()
    rows.sort(key=lambda a: (-a.priority_score, a.appointment_time))
    out: list[dict] = []
    for a in rows:
        p = db.session.get(User, a.patient_id)
        out.append(
            {
                "appointment": a,
                "patient_name": p.name if p else f"#{a.patient_id}",
                "time_label": a.appointment_time.strftime("%H:%M"),
            }
        )
    return out


def admin_appointments_full_rows() -> list[dict]:
    rows = Appointment.query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc(),
    ).all()
    out: list[dict] = []
    for a in rows:
        p = db.session.get(User, a.patient_id)
        d = db.session.get(User, a.doctor_id)
        out.append(
            {
                "appointment": a,
                "patient_name": p.name if p else "?",
                "doctor_name": d.name if d else "?",
            }
        )
    return out
