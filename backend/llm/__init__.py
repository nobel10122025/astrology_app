"""
LLM layer for the Vedic Astrology agent.

This is the ONLY place in the backend that calls a large language model.
Everything else (chart building, scoring, dasha, rule evaluation) is pure,
deterministic Python. The LLM is used solely to turn a structured, already-
computed "reading" into a warm, age-aware narrative.

Three providers are supported behind one `narrate()` dispatcher:
  - "groq"      -> Groq free tier   (llm.groq_narrator)      [default]
  - "anthropic" -> Claude           (llm.response_builder)
  - "ollama"    -> local model      (llm.ollama_narrator)    [no API key]
Pick per request, or set LLM_PROVIDER in the environment.
"""

import os

from llm.reading_adapter import assemble_reading
from llm.response_builder import build_reading_narrative

__all__ = ["narrate", "build_reading_narrative", "assemble_reading"]


def narrate(reading: dict, provider: str = None) -> dict:
    """Narrate a structured reading with the chosen provider.

    provider precedence: explicit arg -> LLM_PROVIDER env -> "groq".
    """
    provider = (provider or os.environ.get("LLM_PROVIDER") or "groq").lower()
    if provider == "anthropic":
        return build_reading_narrative(reading)
    if provider == "groq":
        from llm.groq_narrator import build_reading_narrative_groq
        return build_reading_narrative_groq(reading)
    if provider == "ollama":
        from llm.ollama_narrator import build_reading_narrative_ollama
        return build_reading_narrative_ollama(reading)
    raise ValueError(f"Unknown LLM provider: {provider!r}")
