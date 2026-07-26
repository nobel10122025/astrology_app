"""
Narrative blueprint - exposes the single LLM call over HTTP.

POST /api/narrative
Body (either form works):
  A) Pre-built reading:
     { "reading": { "current_age": 31, "active_dasha": "...", "domains": [...] } }
  B) Raw calculate output to adapt server-side:
     {
       "calculation": <the /api/calculate response>,   # or send those keys at top level
       "dasha": <the /api/dasha-info `dasha` object>,   # optional
       "current_age": 31,                                # optional
       "name": "..."                                     # optional
     }

Response:
  { "status": "success", "reading": {...}, "narrative": {opening, domains, closing, disclaimer} }
"""

from flask import Blueprint, jsonify, request

from llm import assemble_reading, build_reading_narrative

narrative_bp = Blueprint("narrative", __name__, url_prefix="/api")


@narrative_bp.route("/narrative", methods=["POST"])
def narrative():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided", "status": "error"}), 400

    reading = data.get("reading")
    if reading is None:
        # Adapt the raw calculate output. Accept it under "calculation" or,
        # for convenience, treat the whole body as the calculate response.
        calc = data.get("calculation") or data
        reading = assemble_reading(
            calc,
            dasha=data.get("dasha"),
            current_age=data.get("current_age"),
            name=data.get("name"),
        )

    if not reading.get("domains"):
        return jsonify(
            {"error": "Reading has no domains to narrate", "status": "error"}
        ), 400

    try:
        result = build_reading_narrative(reading)
    except Exception as e:  # surface model/config errors without 500-crashing silently
        return jsonify({"error": str(e), "status": "error"}), 500

    return jsonify({"status": "success", "reading": reading, "narrative": result}), 200
