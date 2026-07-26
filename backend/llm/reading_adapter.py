"""
Reading adapter.

Bridges what the backend produces TODAY (the /api/calculate response +
optional dasha info) into the `reading` structure that response_builder wants.

This is deliberately a thin, defensive translation layer. When the real agent
pool + timing engine land, agents will emit these domain findings directly and
this adapter shrinks to a passthrough. Until then it lets us wire the LLM end
to end against the existing data.
"""


def _house_score(house_obj):
    if isinstance(house_obj, dict):
        return house_obj.get("final_score")
    return None


def _planet_score(planet_obj):
    if isinstance(planet_obj, dict):
        return planet_obj.get("final_score")
    return None


def _lord(lord_obj):
    """A house-lord entry looks like {'planet': 'jupiter', 'score': <row|None>}."""
    if not isinstance(lord_obj, dict):
        return None
    score_row = lord_obj.get("score")
    return {
        "planet": lord_obj.get("planet"),
        "score": _planet_score(score_row) if isinstance(score_row, dict) else None,
    }


def _summarize_block(block):
    """Flatten a relationship/marriage block into {label: score-ish} details."""
    if not isinstance(block, dict):
        return {}
    out = {}
    for key, value in block.items():
        if not isinstance(value, dict):
            continue
        if "final_score" in value:  # a house or planet row
            out[key] = value["final_score"]
        elif "score" in value and "planet" in value:  # a house-lord entry
            out[key] = _lord(value)
    return out


def _avg(values):
    nums = [v for v in values if isinstance(v, (int, float))]
    return round(sum(nums) / len(nums), 2) if nums else None


# Maps a relationship key from the calculate response to a domain descriptor.
_RELATIONSHIP_DOMAINS = {
    "spouse": ("marriage", "marriage spouse wedding partnership"),
    "children": ("children", "children baby pregnancy son daughter"),
    "father": ("father", "father dad paternal"),
    "mother": ("mother", "mother mom maternal"),
    "younger_brother": ("younger_brother", "younger brother sibling"),
    "elder_brother": ("elder_brother", "elder brother sibling"),
    "younger_sister": ("younger_sister", "younger sister sibling"),
    "elder_sister": ("elder_sister", "elder sister sibling"),
}


def _house_row(house_results, house_num):
    for row in house_results or []:
        if row.get("house") == house_num:
            return row
    return None


def assemble_reading(calc, dasha=None, current_age=None, name=None):
    """
    Build a `reading` dict from the /api/calculate response.

    Args:
        calc: the JSON object returned by POST /api/calculate.
        dasha: optional dasha info (from /api/dasha-info -> `dasha`).
        current_age: optional int.
        name: optional person's name.

    Returns:
        reading dict consumable by response_builder.build_reading_narrative.
    """
    calc = calc or {}
    house_results = calc.get("house_results", [])
    relationship = calc.get("relationship", {}) or {}
    marriage = calc.get("marriage", {}) or {}

    domains = []

    # --- Career / profession (houses 10, 2, 11) ---
    career_scores = [
        _house_score(_house_row(house_results, h)) for h in (10, 2, 11)
    ]
    domains.append(
        {
            "domain": "profession",
            "topic": "profession career job work",
            "score": _avg(career_scores),
            "timing": "GENERAL",
            "details": {
                "tenth_house": _house_score(_house_row(house_results, 10)),
                "second_house": _house_score(_house_row(house_results, 2)),
                "eleventh_house": _house_score(_house_row(house_results, 11)),
                "profession_hint": (calc.get("prediction", {}) or {}).get("profession"),
            },
        }
    )

    # --- Marriage (from lagna + key indicators) ---
    marriage_details = {
        "from_lagna": _summarize_block(marriage.get("from_lagna")),
        "key_indicators": _summarize_block(marriage.get("key_indicators")),
    }
    spouse_block = relationship.get("spouse")
    if spouse_block:
        marriage_details["spouse"] = _summarize_block(spouse_block)
    domains.append(
        {
            "domain": "marriage",
            "topic": "marriage spouse wedding partnership",
            "score": _house_score(_house_row(house_results, 7)),
            "timing": "GENERAL",
            "details": marriage_details,
        }
    )

    # --- Relationships & children (one domain per relation) ---
    for key, (domain_name, topic) in _RELATIONSHIP_DOMAINS.items():
        if domain_name == "marriage":  # already handled above
            continue
        block = relationship.get(key)
        if not block:
            continue
        details = _summarize_block(block)
        domains.append(
            {
                "domain": domain_name,
                "topic": topic,
                "score": _avg(
                    [v for v in details.values() if isinstance(v, (int, float))]
                ),
                "timing": "GENERAL",
                "details": details,
            }
        )

    # --- Finance / wealth (houses 2, 11) ---
    domains.append(
        {
            "domain": "finance",
            "topic": "finance wealth money income gains",
            "score": _avg(
                [_house_score(_house_row(house_results, h)) for h in (2, 11)]
            ),
            "timing": "GENERAL",
            "details": {
                "second_house": _house_score(_house_row(house_results, 2)),
                "eleventh_house": _house_score(_house_row(house_results, 11)),
            },
        }
    )

    active_dasha = None
    if isinstance(dasha, dict):
        lord = dasha.get("lord")
        antar = (dasha.get("current_antardasha") or {}).get("lord") if isinstance(
            dasha.get("current_antardasha"), dict
        ) else None
        if lord:
            active_dasha = f"{lord.title()} Mahadasa"
            if antar:
                active_dasha += f", {antar.title()} Antardasa"

    return {
        "name": name,
        "current_age": current_age,
        "active_dasha": active_dasha,
        "domains": domains,
    }
