"""
Profession planner.

The main agent is a deterministic PLANNER: given the person's age it decides the
life stage and which tools to trigger. This keeps the "which tools run" decision
explicit and auditable - a child chart skips timing entirely; a mid-career chart
runs the full set.

Life stages (years) - judgment calls, tune against known charts:
    child (< 14)  -> aptitude only (no timing, no score)
    youth (14-30) -> field forming + when it establishes
    mid   (30-55) -> current field + possible shift
    late  (55+)   -> consolidation / second-innings

By default the LLM decides the plan (TOOL_PLANNER=llm); this table is the
deterministic fallback used when the LLM is unavailable, or when
TOOL_PLANNER=rule.
"""

import os

CHILD_MAX = 14
YOUTH_MAX = 30
LATE_MIN = 55

# Which tools each stage triggers. career_significators + field_resolver run in
# every plan (they answer who/what and need no timeline).
TOOL_PLANS = {
    "child": ["career_significators", "field_resolver"],
    "youth": ["career_significators", "strength", "career_arc", "timing", "field_resolver"],
    "mid":   ["career_significators", "strength", "career_arc", "dasha_favourability", "timing", "field_resolver"],
    "late":  ["career_significators", "strength", "career_arc", "dasha_favourability", "timing", "field_resolver"],
}


def life_stage(age):
    """Map an age to a career life stage. Unknown age -> 'youth' (natal,
    forward-looking; no timeline is available anyway)."""
    if age is None:
        return "youth"
    if age < CHILD_MAX:
        return "child"
    if age < YOUTH_MAX:
        return "youth"
    if age < LATE_MIN:
        return "mid"
    return "late"


def plan(age):
    """Deterministic plan: returns (life_stage, [tool_name, ...]) for an age."""
    stage = life_stage(age)
    return stage, TOOL_PLANS[stage]


def resolve_plan(plan_context):
    """Decide the plan, LLM-first with a deterministic fallback.

    TOOL_PLANNER=llm  (default) -> the LLM picks the tools; on any failure
                                    (no key, rate limit, bad output) fall back to
                                    the age-based table.
    TOOL_PLANNER=rule            -> always use the age-based table.

    Returns (life_stage, tools, kind, reasoning) where kind is
    'llm' | 'rule-fallback' | 'rule'.
    """
    age = plan_context.get("age")
    mode = os.environ.get("TOOL_PLANNER", "llm").lower()

    if mode == "llm":
        try:
            from llm.tool_planner import plan_tools
            res = plan_tools(plan_context)
            return res["life_stage"], res["tools"], "llm", res.get("reasoning")
        except Exception as e:  # noqa: BLE001 - any failure -> deterministic plan
            stage, tools = plan(age)
            return stage, tools, "rule-fallback", f"LLM planner unavailable: {e}"

    stage, tools = plan(age)
    return stage, tools, "rule", None
