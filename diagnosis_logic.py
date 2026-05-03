"""Deterministic risk scoring from patient-entered metrics — not a licensed medical device."""

from __future__ import annotations

from typing import Any

TEST_TYPES = frozenset({"heart", "diabetes", "thyroid"})


def tier_three_band(score: int, low_max: int, mid_max: int) -> str:
    if score <= low_max:
        return "Low Risk"
    if score <= mid_max:
        return "Medium Risk"
    return "High Risk"


def coerce_bool(raw: Any) -> bool | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    s = str(raw).strip().lower()
    if s in {"yes", "true", "1", "on", "y"}:
        return True
    if s in {"no", "false", "0", "off", "n", ""}:
        return False
    return None


def coerce_positive_num(raw: Any) -> float | None:
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    return v if v >= 0 else None


def coerce_int(raw: Any) -> int | None:
    num = coerce_positive_num(raw)
    if num is None:
        return None
    return int(round(num))


def _in_range(v: int, lo: int, hi: int) -> bool:
    return lo <= v <= hi


def score_heart(payload: dict[str, Any]) -> tuple[int | None, str | None]:
    """Classic heart-disease dataset style fields → integer score + Low/Medium/High."""
    age = coerce_int(payload.get("age"))
    sex = coerce_int(payload.get("sex"))
    cp = coerce_int(payload.get("cp"))
    trestbps = coerce_int(payload.get("trestbps"))
    chol = coerce_int(payload.get("chol"))
    fbs = coerce_int(payload.get("fbs"))
    restecg = coerce_int(payload.get("restecg"))
    thalach = coerce_int(payload.get("thalach"))
    exang = coerce_int(payload.get("exang"))
    oldpeak_raw = coerce_positive_num(payload.get("oldpeak"))
    slope = coerce_int(payload.get("slope"))
    ca = coerce_int(payload.get("ca"))
    thal = coerce_int(payload.get("thal"))

    if any(
        x is None
        for x in (
            age,
            sex,
            cp,
            trestbps,
            chol,
            fbs,
            restecg,
            thalach,
            exang,
            slope,
            ca,
            thal,
            oldpeak_raw,
        )
    ):
        return None, None

    oldpeak = float(oldpeak_raw)

    if not (
        _in_range(sex, 0, 1)
        and _in_range(cp, 0, 3)
        and _in_range(fbs, 0, 1)
        and _in_range(restecg, 0, 2)
        and _in_range(exang, 0, 1)
        and _in_range(slope, 0, 2)
        and _in_range(ca, 0, 3)
        and thal in (3, 6, 7)
        and age > 0
        and 0 <= thalach <= 250
        and trestbps > 0
        and chol > 0
    ):
        return None, None

    pts = 0
    if age >= 65:
        pts += 3
    elif age >= 55:
        pts += 2

    if sex == 1:
        pts += 1

    if cp <= 2:
        pts += 4 - cp

    if trestbps >= 140:
        pts += 2
    elif trestbps >= 130:
        pts += 1

    if chol >= 240:
        pts += 2
    elif chol >= 200:
        pts += 1

    if fbs == 1:
        pts += 1

    if restecg > 0:
        pts += 1

    if thalach <= 130:
        pts += 2
    elif thalach <= 150:
        pts += 1

    if exang == 1:
        pts += 2

    if oldpeak >= 2.5:
        pts += 3
    elif oldpeak >= 1.5:
        pts += 2
    elif oldpeak >= 1.0:
        pts += 1

    if slope == 2:
        pts += 2
    elif slope == 1:
        pts += 1

    pts += ca * 2

    if thal != 3:
        pts += 3

    score_cap = max(0, min(42, pts))
    result = tier_three_band(score_cap, 11, 20)
    return score_cap, result


def score_diabetes(payload: dict[str, Any]) -> tuple[int | None, str | None]:
    age = coerce_int(payload.get("age"))
    glucose = coerce_positive_num(payload.get("glucose"))
    bp = coerce_positive_num(payload.get("bp"))
    skin_raw = coerce_positive_num(payload.get("skinthickness"))
    insulin = coerce_positive_num(payload.get("insulin"))
    bmi = coerce_positive_num(payload.get("bmi"))
    dpf = coerce_positive_num(payload.get("dpf"))

    if any(x is None for x in (age, glucose, bp, skin_raw, insulin, bmi, dpf)):
        return None, None

    skin = int(round(skin_raw))
    pts = 0

    if age >= 65:
        pts += 4
    elif age >= 45:
        pts += 2

    if glucose >= 200:
        pts += 5
    elif glucose >= 140:
        pts += 3
    elif glucose >= 126:
        pts += 2

    if bp >= 100:
        pts += 2
    elif bp >= 85:
        pts += 1

    if skin >= 42:
        pts += 2
    elif skin >= 29:
        pts += 1

    if insulin >= 200:
        pts += 1

    if bmi >= 35:
        pts += 4
    elif bmi >= 30:
        pts += 3
    elif bmi >= 25:
        pts += 2

    if dpf >= 1.25:
        pts += 3
    elif dpf >= 0.75:
        pts += 2
    elif dpf >= 0.45:
        pts += 1

    score_cap = max(0, min(40, pts))
    result = tier_three_band(score_cap, 9, 18)
    return score_cap, result


def score_thyroid(payload: dict[str, Any]) -> tuple[int | None, str | None]:
    tsh = coerce_positive_num(payload.get("tsh"))
    weight_gain = coerce_bool(payload.get("weight_gain"))
    hair_loss = coerce_bool(payload.get("hair_loss"))
    fatigue = coerce_bool(payload.get("fatigue"))
    if any(x is None for x in (tsh, weight_gain, hair_loss, fatigue)):
        return None, None
    s = 0
    if tsh > 5:
        s += 4
    if weight_gain:
        s += 2
    if hair_loss:
        s += 2
    if fatigue:
        s += 2
    return s, tier_three_band(s, 3, 7)


SCORERS = {
    "heart": score_heart,
    "diabetes": score_diabetes,
    "thyroid": score_thyroid,
}


def evaluate(test_type: str, payload: dict[str, Any]) -> tuple[int | None, str | None]:
    fn = SCORERS.get(test_type)
    if fn is None:
        return None, None
    return fn(payload)


def human_label_test_type(test_type: str) -> str:
    return {
        "heart": "Heart Risk",
        "diabetes": "Diabetes Risk",
        "thyroid": "Thyroid Screening",
        "pregnancy": "Pregnancy Screening",
    }.get(test_type, test_type)
