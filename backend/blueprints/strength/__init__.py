"""
Strength blueprint - three-track planet assessment + LLM judgement.

POST /api/planet-strength
Body: {
  "ascendant": {...}, "sun": {...}, ... "ketu": {...},   # same shape as /calculate
  "birth_date": "1993-05-15",   # optional; needed for the dasha context
  "planets": ["saturn", "venus"],  # optional; default = the active maha+bhukti
                                   #   lords, or all placed planets if no dob
  "judge": true,                   # optional (default true); false = packets only
  "model": "..."                   # optional Groq model override
}

Response: {
  status, current_age, active_dasha,
  tithi,                  # the chart's Moon-phase fact sheet
  packets: {planet: {tracks:{bala,sambandha,adhikara}, conflicts, delivers, ...}},
  judgements: {planet: {verdict, dominant_track, cited, delivers, reasoning, ...}}
}

Unlike the single `final_score` the older endpoints expose, this returns the
three tracks UNCOLLAPSED plus the conflicts between them, and (when judging is
on) the LLM's arbitration of those conflicts.
"""

from flask import Blueprint, jsonify, request

from core.chart_context import build_chart_context
from core.dasha_rules import _lords_from_active
from core.strength_tracks import build_packet
from llm.planet_judge import judge_or_fallback
from utils.calculations.tithi import describe as describe_tithi
from utils.constant import PLANETS

strength_bp = Blueprint("strength", __name__, url_prefix="/api")

_REQUIRED = ["ascendant", "sun", "moon", "mars", "mercury",
             "jupiter", "venus", "saturn", "rahu", "ketu"]


def _target_planets(ctx, requested):
    """Which planets to assess: the explicit list, else the active maha+bhukti
    lords, else every placed planet."""
    if requested:
        return [p.lower() for p in requested if p.lower() in ctx.planet_houses]

    maha, bhukti = _lords_from_active(ctx.active_dasha)
    lords = [p for p in (maha, bhukti) if p and p in ctx.planet_houses]
    if lords:
        return lords
    return [p for p in PLANETS if p in ctx.planet_houses]


@strength_bp.route("/planet-strength", methods=["POST"])
def planet_strength():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided", "status": "error"}), 400

    for field in _REQUIRED:
        entry = data.get(field)
        if not isinstance(entry, dict) or not entry.get("house") or not entry.get("degree"):
            return jsonify(
                {"error": f"Missing degree or house for: {field}", "status": "error"}
            ), 400

    try:
        ctx = build_chart_context(data, data.get("birth_date"))
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e), "status": "error"}), 500

    maha, bhukti = _lords_from_active(ctx.active_dasha)
    targets = _target_planets(ctx, data.get("planets"))

    packets = {}
    for p in targets:
        role = "maha" if p == maha else "bhukti" if p == bhukti else "natal"
        packets[p] = build_packet(ctx, p, role=role)

    sun = (ctx.chart.get("sun") or {}).get("degree")
    moon = (ctx.chart.get("moon") or {}).get("degree")

    response = {
        "status": "success",
        "current_age": ctx.current_age,
        "active_dasha": ctx.active_dasha,
        "tithi": describe_tithi(sun, moon) if sun is not None and moon is not None else None,
        "packets": packets,
    }

    if data.get("judge", True):
        response["judgements"] = {
            p: judge_or_fallback(pkt, model=data.get("model"))
            for p, pkt in packets.items()
        }

    return jsonify(response), 200
