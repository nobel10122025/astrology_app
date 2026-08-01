"""
Ollama narrator - a fully local, no-API-key alternative narrator.

Same job and contract as the Groq/Anthropic narrators (takes a structured
`reading`, returns the narrative dict), but calls a local Ollama server through
its OpenAI-compatible endpoint. This lets the whole pipeline run offline with a
small local model (e.g. Gemma) when no cloud key is available.

Reuses the `openai` SDK pointed at Ollama's base URL. Ollama ignores the API key
but the SDK requires a non-empty string, so we pass a placeholder. Model and
endpoint are configurable via OLLAMA_MODEL / OLLAMA_BASE_URL.

The astrology is still fully computed upstream; the model only narrates.
"""

import json
import os

from openai import OpenAI

from llm.groq_narrator import _SHAPE_INSTRUCTION
from llm.response_builder import DISCLAIMER, SYSTEM_PROMPT

# Ollama's OpenAI-compatible endpoint (the /v1 shim), overridable for remote hosts.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
# Small, fast local default. Override with OLLAMA_MODEL (e.g. gemma3:4b, gemma:7b).
DEFAULT_MODEL = "gemma2:2b"

_client = None


def _get_client():
    """Lazily construct the Ollama client so importing this module never starts a
    connection. No real key is needed; the SDK just wants a non-empty string."""
    global _client
    if _client is None:
        api_key = os.environ.get("OLLAMA_API_KEY", "ollama")
        _client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=api_key)
    return _client


def build_reading_narrative_ollama(reading: dict) -> dict:
    """Turn a structured reading into a narrative via a local Ollama model.
    Mirrors llm.response_builder.build_reading_narrative's input/output contract.

    Gemma has no dedicated system role in its chat template; Ollama folds the
    system message into the first user turn, so passing SYSTEM_PROMPT as a system
    message still works. We also repeat the shape instruction inline because
    small local models follow an explicit example more reliably."""
    client = _get_client()
    model = os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)

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
        # Ollama honours OpenAI-style JSON mode; it constrains output to valid JSON.
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("Ollama returned no content")

    data = json.loads(text)
    if "domains" not in data:
        raise RuntimeError(f"Ollama output missing 'domains': {text[:200]}")

    data.setdefault("opening", "")
    data.setdefault("closing", "")
    data["disclaimer"] = DISCLAIMER
    data["model"] = response.model
    return data
