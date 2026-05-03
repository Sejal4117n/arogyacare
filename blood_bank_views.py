"""Blood donation registration and blood request flows."""
from __future__ import annotations

import datetime as dt

from flask import flash, redirect, render_template, request, url_for

from auth import current_user, role_required
from models import BloodDonor, BloodInventory, db

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


def _ensure_blood_inventory_rows() -> None:
    existing = {row.blood_group for row in BloodInventory.query.all()}
    added = False
    for group in BLOOD_GROUPS:
        if group not in existing:
            db.session.add(BloodInventory(blood_group=group, units_available=0, last_updated=dt.datetime.utcnow()))
            added = True
    if added:
        db.session.commit()


def blood_inventory_rows() -> list[BloodInventory]:
    _ensure_blood_inventory_rows()
    return BloodInventory.query.order_by(BloodInventory.blood_group.asc()).all()


def init_blood_bank_views(app):
    @app.route("/blood-donation", methods=["GET", "POST"])
    @role_required("patient")
    def blood_donation():
        me = current_user()
        if me is None:
            return redirect(url_for("auth.login"))

        _ensure_blood_inventory_rows()

        if request.method == "POST":
            donor_name = (request.form.get("donor_name") or "").strip()
            age_raw = (request.form.get("age") or "").strip()
            gender = (request.form.get("gender") or "").strip()
            blood_group = (request.form.get("blood_group") or "").strip().upper()
            phone = (request.form.get("phone") or "").strip()
            city = (request.form.get("city") or "").strip()

            age: int | None = None
            try:
                age = int(age_raw)
            except (TypeError, ValueError):
                age = None

            valid = True
            if len(donor_name) < 2 or not phone or not city:
                valid = False
            if gender not in {"Male", "Female", "Other"}:
                valid = False
            if blood_group not in BLOOD_GROUPS:
                valid = False
            if age is None:
                valid = False

            status = "Eligible" if valid and 18 <= age <= 60 else "Not Eligible"

            donor = BloodDonor(
                patient_id=me.id,
                donor_name=donor_name or me.name,
                age=age or 0,
                gender=gender or "Other",
                blood_group=blood_group if blood_group in BLOOD_GROUPS else "O+",
                phone=phone,
                city=city,
                donated_on=dt.datetime.utcnow(),
                status=status,
            )
            db.session.add(donor)

            if status == "Eligible":
                inv = BloodInventory.query.filter_by(blood_group=blood_group).first()
                if inv is not None:
                    inv.units_available = max(0, int(inv.units_available)) + 1
                    inv.last_updated = dt.datetime.utcnow()
                db.session.commit()
                flash("Thank you for donating blood.", "success")
                return redirect(url_for("blood_donation"))

            db.session.commit()
            flash("You are not eligible.", "warning")
            return redirect(url_for("blood_donation"))

        return render_template(
            "patient/blood_donation.html",
            blood_groups=BLOOD_GROUPS,
        )

    @app.route("/blood-request", methods=["GET", "POST"])
    @role_required("patient")
    def blood_request():
        _ensure_blood_inventory_rows()
        if request.method == "POST":
            patient_name = (request.form.get("patient_name") or "").strip()
            blood_group_needed = (request.form.get("blood_group_needed") or "").strip().upper()
            units_raw = (request.form.get("units_needed") or "").strip()
            try:
                units_needed = int(units_raw)
            except (TypeError, ValueError):
                units_needed = 0

            if len(patient_name) < 2 or blood_group_needed not in BLOOD_GROUPS or units_needed <= 0:
                flash("Please enter valid request details.", "danger")
                return redirect(url_for("blood_request"))

            inv = BloodInventory.query.filter_by(blood_group=blood_group_needed).first()
            if inv is not None and int(inv.units_available) >= units_needed:
                inv.units_available = int(inv.units_available) - units_needed
                inv.last_updated = dt.datetime.utcnow()
                db.session.commit()
                flash("Blood available.", "success")
            else:
                flash("Blood not available.", "danger")
            return redirect(url_for("blood_request"))

        return render_template("patient/blood_request.html", blood_groups=BLOOD_GROUPS)
