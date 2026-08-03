"""
Signification engine - the SEMANTIC (not numeric) layer.

A score can tell you *how good* a career is; it can never tell you it is ISRO or
NASA, or that a doctor is a surgeon vs a psychiatrist. That needs meaning. This
module carries the *significations* (meaning tags) of each planet, each rasi
(sign), and each house, and combines the tags of the career-defining planets
into a ranked list of SPECIFIC fields.

WEIGHTING
    Each career planet's tags are not counted equally. They are weighted by the
    planet's own strength AND by the strength of the house it occupies:

        influence(planet) = PLANET_W * strength(planet) + HOUSE_W * strength(house)

    So a strong planet in a strong house dominates the field detection; a weak
    planet in a weak house barely registers. Every tag that planet contributes
    (its own + its sign's + its house's) is added with that influence weight.

    A field's rank = the summed influence of the tags it matches. This keeps the
    result deterministic and auditable - the tag bag shows exactly how much each
    meaning was reinforced and by which planet.

Examples
    Space research (ISRO/NASA): Sun in the 10th (government) + Mercury in Kanya
      (science + astronomy). If Mercury is exalted, its science/astronomy tags
      carry heavy weight -> space research rises to the top.
    Surgeon: strong Mars (surgery, blood) + Sun (medicine).
    Dermatology / radiology: Mercury (skin, diagnostics) + Rahu (radiation).
    Psychiatry: Moon (mind, psychology) + medicine.

This is a SEED. The quality of the output is the quality of these tables -
expand them with your own astrological knowledge.
"""

from collections import Counter

from core.chart_query import ChartQuery

# How much the planet's own strength vs its occupied house's strength count
# toward a tag's weight. Planet leads; the house modulates.
PLANET_STRENGTH_WEIGHT = 0.6
HOUSE_STRENGTH_WEIGHT = 0.4

# When a strength is unknown, assume neutral so the tag still registers.
NEUTRAL_STRENGTH = 5.0

# --- Planet significations -------------------------------------------------
PLANET_TAGS = {
    "sun":     ["government", "authority", "power", "administration", "politics",
                "medicine", "heart", "bones", "eyes", "vitality"],
    "moon":    ["public", "water", "travel", "care", "mind", "hospitality",
                "psychology", "fluids", "chest"],
    "mars":    ["engineering", "machines", "military", "defence", "surgery",
                "fire", "sports", "blood", "muscles", "accidents"],
    "mercury": ["science", "analysis", "mathematics", "computation",
                "communication", "commerce", "writing", "skin", "nerves",
                "diagnostics", "respiratory"],
    "jupiter": ["knowledge", "law", "teaching", "finance", "advisory",
                "philosophy", "medicine", "liver"],
    "venus":   ["arts", "beauty", "luxury", "entertainment", "vehicles",
                "fashion", "reproductive", "cosmetic"],
    "saturn":  ["labour", "iron", "oil", "mining", "masses", "structure",
                "service", "agriculture", "chronic", "longevity"],
    "rahu":    ["technology", "foreign", "research", "aviation", "unconventional",
                "chemicals", "radiation", "imaging", "toxins"],
    "ketu":    ["research", "spirituality", "investigation", "medicine",
                "subtle-diseases"],
}

# --- Rasi (sign) significations -------------------------------------------
RASI_TAGS = {
    "mesha":      ["leadership", "energy", "defence"],
    "vrishabha":  ["finance", "food", "luxury", "resources"],
    "mithuna":    ["communication", "commerce", "media"],
    "karka":      ["public", "water", "care", "hospitality", "chest"],
    "simha":      ["government", "authority", "power", "administration", "heart"],  # Leo
    "kanya":      ["analysis", "science", "astronomy", "health", "mathematics",
                   "diagnostics"],  # Virgo -> analysis / astronomy / health
    "tula":       ["law", "arts", "trade", "diplomacy"],
    "vrishchika": ["research", "investigation", "chemicals", "surgery", "medicine"],  # Scorpio
    "dhanu":      ["knowledge", "law", "philosophy", "teaching"],
    "makara":     ["structure", "industry", "state", "administration"],
    "kumbha":     ["technology", "science", "innovation", "astronomy"],
    "meena":      ["spirituality", "water", "medicine", "imagination"],
}

# --- House significations (light; mostly life-area) -------------------------
HOUSE_TAGS = {
    1: ["self"],
    2: ["income"],
    6: ["health", "service", "disease"],
    10: ["authority", "status"],
    11: ["gains"],
}

# --- Specific fields, each defined by the tags that typify it ---------------
# The person's weighted tag bag is matched against these; a field's score is the
# summed influence of the tags it matches.
FIELDS = {
    # --- science / government / tech ---
    "space research (ISRO / NASA)": ["government", "science", "astronomy", "analysis", "engineering"],
    "civil service / administration": ["government", "authority", "administration"],
    "defence / military": ["government", "military", "defence", "engineering"],
    "software / IT": ["computation", "analysis", "technology", "communication"],
    "finance / banking": ["finance", "commerce", "mathematics"],
    "law / judiciary": ["law", "knowledge", "authority"],
    "arts / entertainment": ["arts", "beauty", "entertainment"],
    "engineering / manufacturing": ["engineering", "machines", "structure", "industry"],
    "research / academia": ["research", "science", "knowledge", "analysis"],
    # --- medical specializations ---
    "medicine / general physician": ["medicine", "health", "care", "diagnostics"],
    "surgery / surgeon": ["surgery", "medicine", "blood"],
    "dermatology": ["skin", "medicine", "health"],
    "radiology / imaging": ["radiation", "imaging", "diagnostics", "medicine"],
    "psychiatry / psychology": ["psychology", "mind", "medicine", "care"],
    "cardiology": ["heart", "medicine", "surgery"],
}

# A field must match at least this fraction of its own tags to be a candidate.
MIN_MATCH_RATIO = 0.34


def _influence(planet_strength, house_strength):
    """Combine planet strength and occupied-house strength into a 0-10 weight."""
    ps = planet_strength if planet_strength is not None else NEUTRAL_STRENGTH
    hs = house_strength if house_strength is not None else NEUTRAL_STRENGTH
    return PLANET_STRENGTH_WEIGHT * ps + HOUSE_STRENGTH_WEIGHT * hs


def build_profile(planet, rasi, house, weight=1.0):
    """The meaning tags a single career planet contributes - its own + its
    sign's + its house's - each added with the given influence weight."""
    bag = Counter()
    for tag in PLANET_TAGS.get(planet, []):
        bag[tag] += weight
    for tag in RASI_TAGS.get(rasi, []):
        bag[tag] += weight
    for tag in HOUSE_TAGS.get(house, []):
        bag[tag] += weight
    return bag


def resolve_fields(career_planets, ctx, top_n=4):
    """Combine the weighted profiles of the career planets and rank matching
    fields.

    Args:
        career_planets: planets (lowercase) whose significations shape the field.
        ctx: ChartContext (for each planet's rasi, house, and strengths).
        top_n: how many ranked fields to return.

    Returns:
        {
          "tag_bag": {tag: weight, ...},          # rounded influence per tag
          "sources": {tag: [planet, ...], ...},   # which planet gave each tag
          "influence": {planet: weight, ...},     # per-planet influence used
          "influence_parts": {planet: {...}, ...},# strength breakdown (audit)
          "fields": [
             {"field": str, "matched": [tags], "match_count": int,
              "score": float, "ratio": float}, ...
          ],
        }
    """
    q = ChartQuery(ctx)
    bag = Counter()
    sources = {}
    influence = {}
    influence_parts = {}

    for p in career_planets:
        rasi = ctx.chart.get(p, {}).get("rasi")
        house = ctx.planet_houses.get(p)
        house_strength = q.strength(house) if house else None
        w = _influence(q.strength(p), house_strength)
        influence[p] = round(w, 2)
        influence_parts[p] = {
            "planet_strength": q.strength(p),
            "occupied_house": house,
            "house_strength": house_strength,
        }
        prof = build_profile(p, rasi, house, weight=w)
        bag.update(prof)
        for tag in prof:
            sources.setdefault(tag, [])
            if p not in sources[tag]:
                sources[tag].append(p)

    scored = []
    for field, tags in FIELDS.items():
        matched = [t for t in tags if bag.get(t, 0) > 0]
        ratio = len(matched) / len(tags) if tags else 0
        if ratio >= MIN_MATCH_RATIO:
            scored.append({
                "field": field,
                "matched": matched,
                "match_count": len(matched),
                "score": round(sum(bag[t] for t in matched), 2),
                "ratio": round(ratio, 2),
            })

    # Rank by summed influence of matched tags (captures both count AND
    # strength); break ties by raw match count, then ratio.
    scored.sort(key=lambda f: (f["score"], f["match_count"], f["ratio"]), reverse=True)

    return {
        "tag_bag": {t: round(w, 2) for t, w in bag.items()},
        "sources": sources,
        "influence": influence,
        "influence_parts": influence_parts,
        "fields": scored[:top_n],
    }
