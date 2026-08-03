"""
Rule engine.

The only place where knowledge (scores, house lords, planet placements) is
applied to a specific chart on behalf of an agent. Agents declare a checklist;
this module evaluates it. Agents never compute here.

Three pieces:
- ChecklistResolver  -> normalized 0-10 domain score + breakdown
- SpecialFlagInjector -> auto-injected Saturn/Mars/Rahu/Ketu style flags
- AgeEligibilityGate  -> hard "skip / future / ok" decision by age
"""

# Score-engine range is [-5, 15] (see scoring_engine). Map to [0, 10].
_RAW_MIN, _RAW_MAX = -5.0, 15.0


def _normalize(raw):
    norm = (raw - _RAW_MIN) / (_RAW_MAX - _RAW_MIN) * 10.0
    return max(0.0, min(10.0, norm))


class ChecklistResolver:
    """Evaluate a checklist against a ChartContext -> {score, breakdown}."""

    @staticmethod
    def resolve(checklist, ctx):
        breakdown = []
        weighted_sum = 0.0
        total_weight = 0.0

        for item in checklist:
            check = item["check"]
            weight = item.get("weight", 1)
            raw, subject = ChecklistResolver._evaluate(check, item, ctx)

            if raw is None:
                breakdown.append(
                    {"check": check, "subject": subject, "raw": None,
                     "normalized": None, "weight": weight, "note": "no data"}
                )
                continue

            norm = _normalize(raw)
            weighted_sum += norm * weight
            total_weight += weight
            breakdown.append(
                {"check": check, "subject": subject, "raw": round(raw, 2),
                 "normalized": round(norm, 2), "weight": weight}
            )

        score = round(weighted_sum / total_weight, 2) if total_weight else None
        return {"score": score, "breakdown": breakdown}

    @staticmethod
    def _evaluate(check, item, ctx):
        """Return (raw_score, subject_label). raw is on the [-5, 15] scale."""
        if check == "house_strength":
            h = item["house"]
            return ctx.house_scores.get(h), f"house {h}"

        if check == "house_lord_strength":
            h = item["house"]
            lord = ctx.house_lords.get(h)
            raw = ctx.scores.get(lord) if lord else None
            return raw, f"house {h} lord ({lord or 'n/a'})"

        if check == "planet_strength":
            p = item["planet"].lower()
            return ctx.scores.get(p), f"planet {p}"

        if check == "lagna_strength":
            return ctx.house_scores.get(1), "lagna (house 1)"

        if check == "lagna_lord_strength":
            lord = ctx.house_lords.get(1)
            raw = ctx.scores.get(lord) if lord else None
            return raw, f"lagna lord ({lord or 'n/a'})"

        return None, f"unknown check '{check}'"


# Special-rule flags. Each rule is domain-scoped ("*" = all domains) with a
# predicate over the ChartContext. Adding a rule here makes every matching
# agent benefit automatically - the "KBs are the source of truth" property.
# Seeded with profession-relevant rules for the vertical slice; extend freely.
_FLAG_RULES = [
    {
        "domains": ["profession"],
        "flag": "career_discipline_delay",
        "note": "Saturn in the 10th: career is built slowly through discipline; "
                "recognition tends to arrive with maturity rather than early.",
        "when": lambda ctx: ctx.planet_houses.get("saturn") == 10,
    },
    {
        "domains": ["profession"],
        "flag": "unconventional_career",
        "note": "Rahu in the 10th: an unconventional, modern, or foreign-linked "
                "career path is indicated.",
        "when": lambda ctx: ctx.planet_houses.get("rahu") == 10,
    },
    {
        "domains": ["profession"],
        "flag": "authority_career",
        "note": "Sun in the 10th: natural authority and a pull toward leadership "
                "or government-linked work.",
        "when": lambda ctx: ctx.planet_houses.get("sun") == 10,
    },
    {
        "domains": ["profession"],
        "flag": "driven_career",
        "note": "Mars in the 10th: strong drive and ambition in career; suits "
                "action-oriented or technical fields.",
        "when": lambda ctx: ctx.planet_houses.get("mars") == 10,
    },
]


class SpecialFlagInjector:
    @staticmethod
    def inject(domain, ctx):
        flags = []
        for rule in _FLAG_RULES:
            if domain not in rule["domains"] and "*" not in rule["domains"]:
                continue
            try:
                if rule["when"](ctx):
                    flags.append({"flag": rule["flag"], "note": rule["note"]})
            except Exception:
                continue
        return flags


class AgeEligibilityGate:
    """Hard age rules. Agents own their own min/realistic ages."""

    @staticmethod
    def check(current_age, min_age, realistic_age):
        if current_age is None:
            return "ok"  # no birth date -> cannot gate; let the agent run
        if min_age and current_age < min_age:
            return "skip"
        if realistic_age and current_age < realistic_age:
            return "future"
        return "ok"
