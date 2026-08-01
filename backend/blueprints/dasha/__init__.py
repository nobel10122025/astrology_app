"""
Dasha blueprint - the Dasa-Bhukti favourability endpoint.

POST /api/dasha
Body: {
  "ascendant": {...}, "sun": {...}, ... "ketu": {...},   # same shape as /calculate
  "birth_date": "1993-05-15",   # required for the active maha+bhukti period
  "name": "...",                 # optional
  "narrate": true,                # optional (default true); false = no LLM call
  "provider": "ollama"            # optional; groq (default) | anthropic | ollama
}

Response: {
  status, current_age, active_dasha,
  dasha: {                # the 12-rule sub-agent verdict for the CURRENT period
    available, favourable, combined_score, shashtashtaka, pair_reason,
    maha: {lord, score, favourable, anchor, reasons, findings},
    bhukti: {...} | null
  },
  reading,                # structured domain fed to the narrator
  narrative               # LLM output (only if narrate=true)
}

Unlike /api/dasha-info (which returns the raw Vimshottari timeline), this endpoint
returns the JUDGEMENT: is the person's current Dasa-Bhukti favourable, and why.
"""

from flask import Blueprint, jsonify, request

from core.chart_context import build_chart_context
from core.dasha_evaluator import DasaEvaluator
from llm import narrate

dasha_bp = Blueprint("dasha", __name__, url_prefix="/api")

_REQUIRED = ["ascendant", "sun", "moon", "mars", "mercury",
             "jupiter", "venus", "saturn", "rahu", "ketu"]


def _build_reading(ctx, verdict):
    """Wrap the sub-agent verdict in a one-domain reading for the narrator.
    The narrator only turns the already-decided verdict + reasons into words."""
    maha = verdict.get("maha") or {}
    bhukti = verdict.get("bhukti") or None
    return {
        "name": None,
        "current_age": ctx.current_age,
        "active_dasha": ctx.active_dasha,
        "domains": [
            {
                "domain": "dasha",
                "topic": "current mahadasha bhukti period favourability",
                "score": verdict.get("combined_score"),
                "timing": "ACTIVE",
                "details": {
                    "maha_lord": maha.get("lord"),
                    "bhukti_lord": bhukti.get("lord") if bhukti else None,
                    "favourable": verdict.get("favourable"),
                    "shashtashtaka_6_8": verdict.get("shashtashtaka"),
                    "maha_score": maha.get("score"),
                    "bhukti_score": bhukti.get("score") if bhukti else None,
                    "applied_rules": maha.get("reasons", []),
                },
            }
        ],
    }


@dasha_bp.route("/dasha", methods=["POST"])
def dasha():
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
        verdict = DasaEvaluator.active_period(ctx)
    except Exception as e:  # noqa: BLE001 - surface any build/eval failure as 500
        return jsonify({"error": str(e), "status": "error"}), 500

    response = {
        "status": "success",
        "current_age": ctx.current_age,
        "active_dasha": ctx.active_dasha,
        "dasha": verdict,
    }

    if verdict.get("available"):
        reading = _build_reading(ctx, verdict)
        response["reading"] = reading
        if data.get("narrate", True):
            try:
                response["narrative"] = narrate(reading, provider=data.get("provider"))
            except Exception as e:  # noqa: BLE001 - narration is best-effort
                response["narrative_error"] = str(e)

    return jsonify(response), 200
