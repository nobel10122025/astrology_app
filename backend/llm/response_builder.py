"""
Response builder - the single LLM call in the whole system.

Takes a fully-computed, structured `reading` dict (chart context + a list of
per-domain findings) and asks Claude to narrate it in a warm, age-aware tone.
Returns structured JSON: an opening, one narrative per domain, and a closing.

No astrology is *computed* here. The model only interprets numbers and signals
that the deterministic engine already produced.
"""

import json
import os

import anthropic

# Claude Opus 4.8 - most capable; the narration weaves age, dasha timing, and
# multiple domain scores together, which benefits from a strong model.
MODEL = "claude-opus-4-8"

# Hard-coded, non-model disclaimer always appended server-side so it can never
# be dropped or reworded by the model.
DISCLAIMER = (
    "This reading is generated from your Vedic birth chart for reflection and "
    "self-understanding. It is not a substitute for medical, legal, financial, "
    "or professional advice, and nothing here is fixed or guaranteed."
)

SYSTEM_PROMPT = """You are a warm, grounded Vedic astrologer writing a personal reading.

You are given a structured JSON reading that has ALREADY been computed by a
deterministic engine: a chart context (the person's current age and active
dasha period where known) and a list of life domains, each with a numeric
strength score and supporting signals. Your job is ONLY to interpret and
narrate what is given - never invent planetary positions, scores, or events
that are not in the input.

How to write:
- Speak directly to the person ("you"), warmly and plainly. No jargon dumps.
- Be AGE-AWARE. Use `current_age` and `active_dasha` to frame timing. If a
  domain's `timing` says PAST, speak of it as already lived; ACTIVE as a phase
  they are in now; UPCOMING as ahead of them; GENERAL when timing is unknown -
  then speak to the standing tendency without forcing a date.
- When a domain has `age_range` and `dasa_context`, weave that specific window
  and dasha period into the timing naturally (e.g. "around age 32-36, during
  your Saturn-Venus period"). Do not invent a window when these are absent.
- If `special_flags` are present, factor them in gently as texture, not verdict.
- If a domain's details list concrete indications (e.g. `indicated_professions`),
  name two or three of them as examples - do not dump the whole list.
- Interpret the strength score honestly but kindly: higher scores read as ease
  and support, lower scores as friction, effort, or delay - never as doom.
- For sensitive domains (health, children, marriage, family), be especially
  gentle and non-deterministic. Never predict illness, death, infertility, or
  divorce as certainties. Frame as tendencies, timing windows, and areas to
  tend to.
- Keep each domain to 2-4 sentences. Lead with the takeaway.
- Do NOT restate the raw numbers or field names. Translate them into meaning.

Return the reading in the required structured format."""

# Structured-output schema. `timing` mirrors the engine's tags so the frontend
# can style PAST / ACTIVE / UPCOMING differently. GENERAL = no timing resolved.
_NARRATIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "opening": {
            "type": "string",
            "description": "A warm 1-2 sentence opening that sets the tone and, if age is known, situates the person in their current life phase.",
        },
        "domains": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The domain key exactly as given in the input (e.g. 'profession', 'marriage').",
                    },
                    "title": {
                        "type": "string",
                        "description": "A short human-friendly heading for this domain.",
                    },
                    "timing": {
                        "type": "string",
                        "enum": ["PAST", "ACTIVE", "UPCOMING", "GENERAL"],
                    },
                    "narrative": {
                        "type": "string",
                        "description": "2-4 sentence age-aware interpretation of this domain.",
                    },
                },
                "required": ["domain", "title", "timing", "narrative"],
                "additionalProperties": False,
            },
        },
        "closing": {
            "type": "string",
            "description": "A brief, encouraging 1-2 sentence closing.",
        },
    },
    "required": ["opening", "domains", "closing"],
    "additionalProperties": False,
}

_client = None


def _get_client():
    """Lazily construct the Anthropic client so importing this module never
    requires ANTHROPIC_API_KEY to be set (e.g. during tests)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def build_reading_narrative(reading: dict) -> dict:
    """
    Turn a structured reading into a narrative.

    Args:
        reading: {
            "name": str | None,
            "current_age": int | None,
            "active_dasha": str | None,
            "domains": [
                {"domain": str, "topic": str, "score": float | None,
                 "timing": str, "details": dict}, ...
            ],
        }

    Returns:
        {"opening": str, "domains": [{domain, title, timing, narrative}],
         "closing": str, "disclaimer": str, "model": str}
    """
    client = _get_client()

    user_message = (
        "Here is the structured astrological reading as JSON. Narrate it "
        "following the system instructions.\n\n"
        + json.dumps(reading, ensure_ascii=False, indent=2)
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": _NARRATIVE_SCHEMA},
        },
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # With output_config.format, the JSON lands in the text block. Skip any
    # thinking blocks that adaptive thinking may emit first.
    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise RuntimeError("Model returned no text content")

    data = json.loads(text)
    data["disclaimer"] = DISCLAIMER
    data["model"] = response.model
    return data
