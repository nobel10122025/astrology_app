"""
Predict blueprint - the full pipeline endpoint.

POST /api/predict
Body: {
  "ascendant": {...}, "sun": {...}, ... "ketu": {...},   # same shape as /calculate
  "birth_date": "1993-05-15",   # optional, but required for age-aware timing
  "topic": "profession",         # optional; omit to run all agents
  "name": "...",                 # optional
  "narrate": true,                # optional (default true); false = no LLM call
  "provider": "groq"              # optional; "groq" (default) | "anthropic"
}

Response: {
  status, current_age, active_dasha,
  reading,                # structured domains fed to the LLM
  results,                # raw AgentResult objects (incl. skipped)
  narrative               # LLM output (only if narrate=true and domains exist)
}
"""

from flask import Blueprint, jsonify, request

from llm import narrate
from orchestrator.runner import run_prediction

predict_bp = Blueprint("predict", __name__, url_prefix="/api")

_REQUIRED = ["ascendant", "sun", "moon", "mars", "mercury",
             "jupiter", "venus", "saturn", "rahu", "ketu"]


@predict_bp.route("/predict", methods=["POST"])
def predict():
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
        ctx, results, reading = run_prediction(
            data,
            birth_date=data.get("birth_date"),
            topic=data.get("topic"),
            name=data.get("name"),
        )
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

    response = {
        "status": "success",
        "current_age": ctx.current_age,
        "active_dasha": ctx.active_dasha,
        "reading": reading,
        "results": [r.to_dict() for r in results],
    }

    if data.get("narrate", True) and reading.get("domains"):
        try:
            response["narrative"] = narrate(reading, provider=data.get("provider"))
        except Exception as e:
            response["narrative_error"] = str(e)

    return jsonify(response), 200
