"""
Groq narrator - a drop-in alternative to the Anthropic response builder.

Same job, same contract (takes a structured `reading`, returns the narrative
dict), but calls Groq's free-tier OpenAI-compatible endpoint instead of Claude.
Uses the `openai` SDK (already a dependency) pointed at Groq's base URL.

Groq exposes JSON mode via response_format={"type": "json_object"} but does not
enforce a JSON *schema*, so we describe the required shape in the prompt and
validate the essential keys after parsing. The astrology is still fully computed
upstream; the model only narrates.
"""

import json
import os

from llm.llm_client import build_groq_client, resolve_model

# System prompt and disclaimer are shared with the Anthropic builder so both
# providers speak in the same voice. Importing these does NOT construct a client.
from llm.response_builder import DISCLAIMER, SYSTEM_PROMPT

# Strong, free Groq model. Override with GROQ_MODEL if you prefer a smaller/
# faster one (e.g. llama-3.1-8b-instant).
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Groq has no structured-schema mode, so we spell the shape out and require it.
_SHAPE_INSTRUCTION = """Return ONLY a valid JSON object (no markdown, no prose
outside the JSON) with exactly this shape:

{
  "opening": "warm 1-2 sentence opening",
  "domains": [
    {
      "domain": "the domain key exactly as given in the input",
      "title": "short human-friendly heading",
      "timing": "PAST | ACTIVE | UPCOMING | GENERAL",
      "narrative": "2-4 sentence age-aware interpretation"
    }
  ],
  "closing": "brief encouraging 1-2 sentence closing"
}

Include one domains[] entry for every domain in the input, preserving its
`domain` key and `timing` value."""

_client = None


def _get_client():
    """Lazily construct the Groq client (direct, or via Portkey when
    PORTKEY_API_KEY is set) so importing this module never requires a key."""
    global _client
    if _client is None:
        _client = build_groq_client()
    return _client


def build_reading_narrative_groq(reading: dict) -> dict:
    """Turn a structured reading into a narrative via Groq. Mirrors
    llm.response_builder.build_reading_narrative's input/output contract."""
    client = _get_client()
    model = resolve_model(os.environ.get("GROQ_MODEL", DEFAULT_MODEL))

    user_message = (
        "Here is the structured astrological reading as JSON. Narrate it "
        "following the system instructions.\n\n"
        + json.dumps(reading, ensure_ascii=False, indent=2)
        + "\n\n"
        + _SHAPE_INSTRUCTION
    )

    response = client.chat.completions.create(
        model=model,
        temperature=0.7,
        max_tokens=4000,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("Groq returned no content")

    data = json.loads(text)
    if "domains" not in data:
        raise RuntimeError(f"Groq output missing 'domains': {text[:200]}")

    data.setdefault("opening", "")
    data.setdefault("closing", "")
    data["disclaimer"] = DISCLAIMER
    data["model"] = response.model
    return data
