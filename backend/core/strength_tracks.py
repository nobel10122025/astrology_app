"""
Three-track planet assessment - the un-collapsed replacement for `final_score`.

THE PROBLEM WITH ONE NUMBER
    utils.calculations.planet_calulation computes eleven separate components
    and then adds them into a single `final_score` (-5..15). ChartContext keeps
    only that sum, so by the time an agent asks ChartQuery.strength() the
    engine can no longer tell the difference between:

        a planet that is intrinsically powerful but savagely afflicted, and
        a mediocre planet with clean, supportive contacts

    Those two need opposite predictions. Summing them makes them identical.
    Worse, the summed score is then used as the ANCHOR in core.dasha_rules,
    which proceeds to add dig bala (R5), drishti bala (R5) and conjunction
    relations (R9) a SECOND time - all three are already inside the anchor.

THE THREE TRACKS
    A. BALA      - can it deliver?    intrinsic/positional capacity:
                   exaltation, own sign, kendra/kona (sthana bala), dig bala,
                   combustion.
    B. SAMBANDHA - what QUALITY will it deliver?  who touches it, and how:
                   benefic redemption vs malefic corruption, weighted by the
                   toucher's own natal house.
    C. ADHIKARA  - WHAT does it deliver?  the houses it owns and their
                   significations, split good vs bad.

    Each fact is counted in exactly ONE track, which also removes the double
    counting described above.

WHY THE TRACKS ARE NOT AVERAGED
    They contradict each other constantly - a 9th lord wrecked by a Mars
    conjunction, a 6th lord redeemed by a Jupiter aspect. The contradiction IS
    the reading. So this module detects the conflicts explicitly and hands the
    whole evidence packet to core/llm judgement rather than pre-resolving it
    arithmetically. Every fact carries a stable id (B3, A1, ...) so the judge
    can cite what it used and the verdict stays auditable.

RULE SOURCES
    Redemption hierarchy, aspect-over-conjunction, malefic-house weighting and
    the "only the good significations" rule are the user's stated rules; each
    constant below names which rule it encodes.
"""

from dataclasses import asdict, dataclass, field

from core.house_data import (
    DUSTHANA,
    KENDRA,
    TRIKONA,
    bad_of,
    good_of,
    name_of,
    ordinal,
)
from utils.calculations.tithi import describe as describe_tithi
from utils.calculations.utils import (
    calculate_degree_difference,
    check_aspect,
    get_conjunction_level,
    is_combust,
)
from utils.constant import (
    COMBUST_DEGREES,
    PLANET_DEBILITATION,
    PLANET_EXALTATION,
    PLANET_OWN_HOUSES,
    PLANETS,
)

# --- Track B: the redemption hierarchy ------------------------------------
# The user's stated order, strongest first:
#   1. full Moon (last 3 days)   2. Jupiter   3. Venus
#   4. Moon between panchami and dashami
# Mercury is NOT in that list, though the legacy engine treated it as a
# benefic. It is included here as a weak conditional benefic (classical:
# Mercury is benefic only when not itself afflicted) - set to 0.0 to drop it
# entirely, pending confirmation.
REDEEMER_WEIGHT = {
    "full_moon": 1.5,
    "jupiter": 1.2,
    "venus": 1.0,
    "waxing_moon": 0.7,
    "mercury": 0.6,
}

# "the aspect is stronger than conjuction" - applies to redemption AND to
# affliction, since both are contacts.
ASPECT_MULTIPLIER = 1.25
CONJUNCTION_MULTIPLIER = 1.0

# Contact tightness. Conjunction levels come from get_conjunction_level (orb
# bands); aspect levels from check_aspect.
CONJUNCTION_TIGHTNESS = {"very_high": 1.0, "high": 0.85, "medium": 0.6, "less": 0.4}
ASPECT_TIGHTNESS = {"high": 1.0, "medium": 0.7, "negligible": 0.45}

# The planets that corrupt. The user named Mars, Saturn and Rahu; Ketu is
# included at the same weight pending the separate node rules.
AFFLICTER_WEIGHT = {"saturn": 1.2, "mars": 1.2, "rahu": 1.1, "ketu": 0.9}

# "Mars in the 8th is worse than Mars in the 3rd" - an afflicter's damage is
# scaled by the house IT occupies natally. Malefics thrive in the upachaya
# houses (3, 6, 10, 11) and do their worst damage from the dusthanas.
MALEFIC_HOUSE_POTENCY = {
    1: 1.1, 2: 1.0, 3: 0.4, 4: 1.2, 5: 1.3, 6: 0.5,
    7: 1.2, 8: 1.6, 9: 1.3, 10: 0.9, 11: 0.5, 12: 1.4,
}

# Benefics are less house-sensitive, but a benefic in a dusthana still gives
# a muted rescue.
BENEFIC_HOUSE_POTENCY = {
    1: 1.1, 2: 1.0, 3: 0.9, 4: 1.1, 5: 1.2, 6: 0.7,
    7: 1.0, 8: 0.6, 9: 1.2, 10: 1.1, 11: 1.0, 12: 0.7,
}

NEUTRAL_SCORE = 5.0
SCORE_MIN, SCORE_MAX = 0.0, 10.0

# A track at or above / below these reads as clearly good / clearly bad. Used
# only to DETECT conflicts, never to resolve them.
STRONG = 6.5
WEAK = 4.0

RASI_LORD = {}
for _p, _signs in PLANET_OWN_HOUSES.items():
    for _s in _signs:
        RASI_LORD[_s] = _p


def _clamp(v):
    return max(SCORE_MIN, min(SCORE_MAX, v))


@dataclass
class Fact:
    """One piece of evidence. `id` is what the LLM judge cites."""
    id: str
    track: str            # bala | sambandha | adhikara
    kind: str             # exaltation | conjunction | aspect | lordship | ...
    polarity: str         # benefic | malefic | neutral
    weight: float         # signed contribution to its track
    note: str             # human-readable statement of the fact
    detail: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class Track:
    name: str
    score: float
    facts: list = field(default_factory=list)

    def to_dict(self):
        return {"name": self.name, "score": self.score,
                "facts": [f.to_dict() for f in self.facts]}


# --------------------------------------------------------------------------
# Track A - BALA (intrinsic capacity)
# --------------------------------------------------------------------------

def _bala_track(ctx, planet, ids):
    facts = []
    cd = ctx.chart.get(planet) or {}
    rasi, house, degree = cd.get("rasi"), ctx.planet_houses.get(planet), cd.get("degree")

    if rasi and PLANET_EXALTATION.get(planet) == rasi:
        facts.append(Fact(ids(), "bala", "exaltation", "benefic", 2.0,
                          f"{planet} is exalted in {rasi}", {"rasi": rasi}))
    elif rasi and PLANET_DEBILITATION.get(planet) == rasi:
        facts.append(Fact(ids(), "bala", "debilitation", "malefic", -2.0,
                          f"{planet} is debilitated in {rasi}", {"rasi": rasi}))
    elif rasi and rasi in PLANET_OWN_HOUSES.get(planet, []):
        facts.append(Fact(ids(), "bala", "own_sign", "benefic", 1.5,
                          f"{planet} is in its own sign {rasi}", {"rasi": rasi}))

    # Sthana bala - angular/trinal placement.
    if house in KENDRA and planet not in ("rahu", "ketu"):
        facts.append(Fact(ids(), "bala", "sthana_bala", "benefic", 1.0,
                          f"{planet} occupies kendra {house} ({name_of(house)})",
                          {"house": house}))
    elif house in TRIKONA and planet not in ("rahu", "ketu"):
        facts.append(Fact(ids(), "bala", "sthana_bala", "benefic", 1.0,
                          f"{planet} occupies trikona {house} ({name_of(house)})",
                          {"house": house}))
    elif house in DUSTHANA:
        facts.append(Fact(ids(), "bala", "sthana_bala", "malefic", -1.0,
                          f"{planet} occupies dusthana {house} ({name_of(house)})",
                          {"house": house}))

    # Dig bala - counted ONCE, here (core.dasha_rules R5 must not re-add it).
    from core.dasha_rules import DIG_BALA_STRONG_HOUSE
    strong = DIG_BALA_STRONG_HOUSE.get(planet)
    if strong and house:
        weak = ((strong - 1 + 6) % 12) + 1
        if house == strong:
            facts.append(Fact(ids(), "bala", "dig_bala", "benefic", 1.0,
                              f"{planet} has full dig bala in the {ordinal(strong)}",
                              {"house": house}))
        elif house == weak:
            facts.append(Fact(ids(), "bala", "dig_bala", "malefic", -1.0,
                              f"{planet} has no dig bala in the {ordinal(weak)}",
                              {"house": house}))

    # Combustion destroys capacity, so it belongs to bala, not sambandha.
    sun_deg = (ctx.chart.get("sun") or {}).get("degree")
    if planet != "sun" and degree is not None and sun_deg is not None:
        limit = COMBUST_DEGREES.get(planet)
        level = is_combust(degree, sun_deg, limit)
        if level == "high":
            facts.append(Fact(ids(), "bala", "combustion", "malefic", -2.0,
                              f"{planet} is deeply combust (within 3deg of the Sun)"))
        elif level == "low":
            facts.append(Fact(ids(), "bala", "combustion", "malefic", -1.0,
                              f"{planet} is combust (within {limit}deg of the Sun)"))

    score = _clamp(NEUTRAL_SCORE + sum(f.weight for f in facts))
    return Track("bala", round(score, 2), facts)


# --------------------------------------------------------------------------
# Track B - SAMBANDHA (who touches it, and how)
# --------------------------------------------------------------------------

def _moon_role(ctx):
    """What kind of benefic (if any) the Moon is in this chart, per the tithi
    rules. Returns (role, tithi_fact_sheet) where role is one of
    'full_moon' | 'waxing_moon' | None."""
    sun = (ctx.chart.get("sun") or {}).get("degree")
    moon = (ctx.chart.get("moon") or {}).get("degree")
    if sun is None or moon is None:
        return None, None
    t = describe_tithi(sun, moon)
    if t["is_full_moon"]:
        return "full_moon", t
    if t["band"] == "benefic":
        return "waxing_moon", t
    return None, t


def _contact(ctx, planet, other):
    """How `other` touches `planet`: ('conjunction'|'aspect', tightness) or None.
    Aspect is checked first because it ranks above conjunction."""
    pd = (ctx.chart.get(planet) or {}).get("degree")
    od = (ctx.chart.get(other) or {}).get("degree")
    if pd is None or od is None:
        return None

    level = check_aspect(other, od, pd)
    if level != "none":
        return "aspect", ASPECT_TIGHTNESS.get(level, 0.4), level

    conj = get_conjunction_level(calculate_degree_difference(pd, od))
    if conj != "none":
        return "conjunction", CONJUNCTION_TIGHTNESS.get(conj, 0.4), conj
    return None


def _sambandha_track(ctx, planet, ids):
    facts = []
    moon_role, tithi = _moon_role(ctx)

    for other in PLANETS:
        if other == planet or other not in ctx.planet_houses:
            continue

        contact = _contact(ctx, planet, other)
        if contact is None:
            continue
        kind, tightness, level = contact
        other_house = ctx.planet_houses.get(other)

        # --- the Moon: gated on light -------------------------------------
        if other == "moon":
            if kind == "aspect" and not (tithi or {}).get("can_aspect"):
                # "this cresent moon has no aspect power as it has no light"
                facts.append(Fact(ids(), "sambandha", "moon_aspect_void", "neutral", 0.0,
                                  f"Moon aspects {planet} but is dark "
                                  f"({tithi['tithi_name']}) - no aspect power",
                                  {"tithi": tithi}))
                continue
            if moon_role:
                w = (REDEEMER_WEIGHT[moon_role] * tightness
                     * (ASPECT_MULTIPLIER if kind == "aspect" else CONJUNCTION_MULTIPLIER)
                     * tithi["benefic_weight"] / 2.0)
                facts.append(Fact(ids(), "sambandha", f"benefic_{kind}", "benefic",
                                  round(w, 3),
                                  f"{tithi['tithi_name']} Moon "
                                  f"{'aspects' if kind == 'aspect' else 'is conjunct'} "
                                  f"{planet} (rank: {moon_role})",
                                  {"tithi": tithi, "level": level}))
            elif kind == "conjunction" and (tithi or {}).get("malefic_weight"):
                w = -tithi["malefic_weight"] * tightness
                facts.append(Fact(ids(), "sambandha", "malefic_conjunction", "malefic",
                                  round(w, 3),
                                  f"dark Moon ({tithi['tithi_name']}) is conjunct "
                                  f"{planet} - afflicts it",
                                  {"tithi": tithi, "level": level}))
            continue

        # --- benefic redeemers --------------------------------------------
        if other in ("jupiter", "venus", "mercury"):
            base = REDEEMER_WEIGHT[other]
            if base <= 0:
                continue
            w = (base * tightness
                 * (ASPECT_MULTIPLIER if kind == "aspect" else CONJUNCTION_MULTIPLIER)
                 * BENEFIC_HOUSE_POTENCY.get(other_house, 1.0))
            facts.append(Fact(ids(), "sambandha", f"benefic_{kind}", "benefic",
                              round(w, 3),
                              f"{other} (in the {ordinal(other_house)}) "
                              f"{'aspects' if kind == 'aspect' else 'is conjunct'} "
                              f"{planet} - {level} contact",
                              {"from": other, "from_house": other_house,
                               "level": level, "contact": kind}))
            continue

        # --- malefic afflicters -------------------------------------------
        if other in AFFLICTER_WEIGHT:
            potency = MALEFIC_HOUSE_POTENCY.get(other_house, 1.0)
            w = -(AFFLICTER_WEIGHT[other] * tightness
                  * (ASPECT_MULTIPLIER if kind == "aspect" else CONJUNCTION_MULTIPLIER)
                  * potency)
            facts.append(Fact(ids(), "sambandha", f"malefic_{kind}", "malefic",
                              round(w, 3),
                              f"{other} (in the {ordinal(other_house)} - {name_of(other_house)}) "
                              f"{'aspects' if kind == 'aspect' else 'is conjunct'} "
                              f"{planet} - {level} contact, house potency {potency}",
                              {"from": other, "from_house": other_house,
                               "level": level, "contact": kind,
                               "house_potency": potency}))

    score = _clamp(NEUTRAL_SCORE + sum(f.weight for f in facts))
    return Track("sambandha", round(score, 2), facts)


# --------------------------------------------------------------------------
# Track C - ADHIKARA (what it owns, hence what it delivers)
# --------------------------------------------------------------------------

def _adhikara_track(ctx, planet, ids):
    facts = []
    owned = sorted(h for h, l in ctx.house_lords.items() if l == planet)

    if not owned:
        facts.append(Fact(ids(), "adhikara", "no_lordship", "neutral", 0.0,
                          f"{planet} owns no house (node) - judge it by its "
                          f"dispositor and occupancy instead"))
        return Track("adhikara", NEUTRAL_SCORE, facts), owned

    net = 0.0
    for h in owned:
        if h in TRIKONA:
            net += 1.0
            pol, w = "benefic", 1.0
        elif h in DUSTHANA:
            net -= 1.0
            pol, w = "malefic", -1.0
        elif h in KENDRA:
            pol, w = "neutral", 0.0
        else:
            pol, w = "neutral", 0.0
        facts.append(Fact(ids(), "adhikara", "lordship", pol, w,
                          f"{planet} owns the {ordinal(h)} ({name_of(h)})",
                          {"house": h, "good": good_of([h]), "bad": bad_of([h])}))

    score = _clamp(NEUTRAL_SCORE + net)
    return Track("adhikara", round(score, 2), facts), owned


# --------------------------------------------------------------------------
# Conflicts - the whole point of keeping the tracks apart
# --------------------------------------------------------------------------

def _conflicts(bala, sambandha, owned):
    out = []
    owns_good = any(h in TRIKONA for h in owned)
    owns_bad = any(h in DUSTHANA for h in owned)

    if bala.score >= STRONG and sambandha.score <= WEAK:
        out.append({
            "type": "capable_but_afflicted",
            "note": "strong intrinsic bala but corrupted contacts - it has the "
                    "capacity to act, and the results arrive damaged",
        })
    if bala.score <= WEAK and sambandha.score >= STRONG:
        out.append({
            "type": "weak_but_supported",
            "note": "little intrinsic strength but clean benefic support - "
                    "results are good in quality but small in scale",
        })
    if owns_bad and sambandha.score >= STRONG:
        out.append({
            "type": "dusthana_lord_redeemed",
            "note": "owns a dusthana but is redeemed by benefics - per the rule, "
                    "it gives ONLY the good significations of the houses it owns",
            "delivers": good_of(owned),
        })
    if owns_good and sambandha.score <= WEAK:
        out.append({
            "type": "trikona_lord_corrupted",
            "note": "owns a trikona but is afflicted - the good houses it rules "
                    "are damaged; expect their bad significations",
            "delivers": bad_of(owned),
        })
    return out


def _delivers(sambandha, owned):
    """Which side of its houses the planet actually gives.

    The rule: a redeemed planet "only gives the good things which belong to
    that house". So the sambandha track - not the lordship - decides the sign
    of the delivery.
    """
    if not owned:
        return {"side": "n/a", "significations": []}
    if sambandha.score >= STRONG:
        return {"side": "good", "significations": good_of(owned)}
    if sambandha.score <= WEAK:
        return {"side": "bad", "significations": bad_of(owned)}
    return {"side": "mixed",
            "significations": good_of(owned) + bad_of(owned)}


# --------------------------------------------------------------------------
# The evidence packet
# --------------------------------------------------------------------------

def build_packet(ctx, planet, role="maha"):
    """The full three-track evidence packet for one planet.

    This is what goes to the LLM judge. It contains FACTS (each with a citable
    id) and detected CONFLICTS - never a pre-resolved verdict.
    """
    counter = {"n": 0}

    def next_id():
        counter["n"] += 1
        return f"F{counter['n']}"

    bala = _bala_track(ctx, planet, next_id)
    sambandha = _sambandha_track(ctx, planet, next_id)
    adhikara, owned = _adhikara_track(ctx, planet, next_id)

    cd = ctx.chart.get(planet) or {}
    is_node = planet in ("rahu", "ketu")

    return {
        "planet": planet,
        "role": role,
        "placement": {
            "rasi": cd.get("rasi"),
            "house": ctx.planet_houses.get(planet),
            "house_name": name_of(ctx.planet_houses.get(planet)),
            "degree_in_sign": round(cd["degree"] % 30, 2) if cd.get("degree") is not None else None,
            "dispositor": RASI_LORD.get(cd.get("rasi")),
        },
        "tracks": {
            "bala": bala.to_dict(),
            "sambandha": sambandha.to_dict(),
            "adhikara": adhikara.to_dict(),
        },
        "houses_owned": owned,
        "delivers": _delivers(sambandha, owned),
        "conflicts": _conflicts(bala, sambandha, owned),
        "is_node": is_node,
        "node_rules_pending": is_node,
        "legacy_score": ctx.scores.get(planet),
    }


def build_all(ctx, planets=None):
    """Packets for every planet in the chart, keyed by planet."""
    pool = planets or [p for p in PLANETS if p in ctx.planet_houses]
    return {p: build_packet(ctx, p) for p in pool}
