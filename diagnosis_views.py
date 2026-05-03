"""Patient risk-checklist hub (heart, diabetes, thyroid); results stored in diagnosis_reports."""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from auth import current_user, role_required
from diagnosis_logic import TEST_TYPES, evaluate, human_label_test_type
from models import DiagnosisReport, db

diagnosis_bp = Blueprint("diagnosis", __name__)


@diagnosis_bp.route("/diagnosis")
@role_required("patient")
def diagnosis_home():
    return render_template("diagnosis/index.html")


@diagnosis_bp.route("/diagnosis/submit", methods=["POST"])
@role_required("patient")
def diagnosis_submit():
    me = current_user()
    if not me:
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    test_type = (body.get("test_type") or "").strip().lower()
    if test_type not in TEST_TYPES:
        return jsonify({"ok": False, "error": "Unknown test type"}), 400

    score, result = evaluate(test_type, body)
    if score is None or result is None:
        return jsonify({"ok": False, "error": "Missing or invalid fields"}), 400

    row = DiagnosisReport(
        patient_id=me.id,
        test_type=test_type,
        score=score,
        result=result,
    )
    db.session.add(row)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "test_type": test_type,
            "test_label": human_label_test_type(test_type),
            "score": score,
            "result": result,
        }
    )


def init_diagnosis(app):
    """Register blueprint on the app."""
    app.register_blueprint(diagnosis_bp)
