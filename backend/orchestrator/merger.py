"""
Merger.

Collects AgentResults, drops skipped ones, sorts by timing (ACTIVE first) then
confidence, and shapes them into the `reading` dict that the LLM response
builder consumes.
"""

_TIMING_ORDER = {"ACTIVE": 0, "UPCOMING": 1, "GENERAL": 2, "PAST": 3}


def merge(results):
    live = [r for r in results if not r.skipped]
    live.sort(key=lambda r: (_TIMING_ORDER.get(r.timing, 2), -(r.confidence or 0)))
    return live


def build_reading(ctx, results, name=None):
    domains = []
    for r in merge(results):
        domains.append(
            {
                "domain": r.domain,
                "topic": " ".join(r.topics),
                "score": r.score,
                "timing": r.timing,
                "age_range": r.age_range,
                "dasa_context": r.dasa_context,
                "special_flags": [f.get("note") for f in r.special_flags],
                "confidence": r.confidence,
                "details": r.detail,
            }
        )
    return {
        "name": name,
        "current_age": ctx.current_age,
        "active_dasha": ctx.active_dasha,
        "domains": domains,
    }
