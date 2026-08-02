"""
LLM tool-planner - the LLM decides WHICH tools the main agent runs.

This is a deliberately narrow use of an LLM: it does NOT do astrology. Given the
person's age and a few chart facts, it chooses the life stage and which optional
analysis tools to trigger, from a fixed catalog. The tools themselves stay
deterministic, so the numbers never change between runs - only the *selection of
analyses* is LLM-driven.

Two tools are MANDATORY (they answer who/what and need no timeline) and are
always run, so they are not offered to the model. The model only picks among the
OPTIONAL tools, and its output is validated against the known set.

If the LLM is unavailable (no key, rate limit, error), the caller falls back to
the deterministic age-based plan.
"""

import json
import os

from llm.llm_client import build_groq_client

DEFAULT_MODEL = "llama-3.3-70b-versatile"

VALID_STAGES = ["child", "youth", "mid", "late"]

# Always run - not offered to the model.
MANDATORY_TOOLS = ["career_significators", "field_resolver"]

# The optional tools the LLM chooses among, with guidance on when each helps.
TOOL_CATALOG = {
    "strength": "Scores how strong and supportive the career is (0-10). Usually skip for a young child whose career has not formed.",
    "career_arc": "Builds the life timeline of career fields and detects a future career shift. Needs a dasha timeline; most useful from youth onward.",
    "dasha_favourability": "Judges whether the next dasha periods are favourable. Most useful in mid/late career to assess a shift.",
    "timing": "Places the career in a PAST/ACTIVE/UPCOMING age window. Needs a dasha timeline.",
}
OPTIONAL_TOOLS = list(TOOL_CATALOG)

_SYSTEM = """You are the planner for a Vedic career-prediction system. You do NOT
do astrology. Your only job: given a person's age and a few chart facts, choose
(1) the life stage and (2) which OPTIONAL analysis tools to run.

Life stages:
- child (< 14): career not formed - predict aptitude only; usually no timing/score tools.
- youth (14-30): career forming - predict the field and when it establishes.
- mid (30-55): established - current field plus a possible shift.
- late (55+): consolidation / second-innings.

Choose tools that fit the stage and the available facts (e.g. do not choose
timeline tools when has_dasha_timeline is false). Two tools (career_significators,
field_resolver) always run and are not your choice.

Return ONLY JSON:
{"life_stage": "child|youth|mid|late",
 "tools": [subset of the offered optional tools],
 "reasoning": "one short sentence"}"""

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = build_groq_client()
    return _client


def plan_tools(plan_context, provider=None):
    """Ask the LLM which tools to run.

    Args:
        plan_context: {age, has_dasha_timeline, num_career_planets, active_dasha}
        provider: reserved; currently Groq only.

    Returns:
        {"life_stage": str, "tools": [MANDATORY + chosen optional], "reasoning": str}

    Raises on any LLM/parse error so the caller can fall back deterministically.
    """
    client = _get_client()
    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

    catalog_text = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_CATALOG.items())
    user = (
        "Chart facts:\n"
        + json.dumps(plan_context, ensure_ascii=False)
        + "\n\nOptional tools you may choose from:\n"
        + catalog_text
    )

    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        max_tokens=500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    data = json.loads(resp.choices[0].message.content)

    stage = data.get("life_stage")
    if stage not in VALID_STAGES:
        raise ValueError(f"LLM returned invalid life_stage: {stage!r}")

    chosen = [t for t in data.get("tools", []) if t in OPTIONAL_TOOLS]
    tools = MANDATORY_TOOLS + chosen
    return {
        "life_stage": stage,
        "tools": tools,
        "reasoning": (data.get("reasoning") or "").strip(),
    }
