"""
Point-scale planet scoring engine (0-100 / 0-200 frame).
=======================================================

WHY THIS EXISTS
    The live /api/calculate engine scores every influence as a flat integer
    (+1 / +2), which is source-blind: a full-Moon aspect, a Jupiter aspect and
    a Mercury conjunction all collapse to +2. This module replaces that with a
    weighted point model where each factor carries its own magnitude, so a full
    Moon (100) and Jupiter (80) never read as equal.

    It produces the SAME three tracks the UI already shows, but on the new
    scale:

      Track 1  Subathuvam / Papathuvam  - benefic & malefic CONTACTS (aspect /
               conjunction), combustion, and the Moon's tithi-driven effect.
               A net signed value: positive = blessed, negative = afflicted.
      Track 2  Sthana / Dig balam       - the planet's own dignity (exalted,
               moolatrikona, own, friend, neutral, enemy, debilitated, or
               neecha-bhanga) PLUS dig bala. Capped at 200.

DESIGN NOTES
    - EVERY tunable number lives in POINTS below. Change scoring by editing
      that block; the logic never hard-codes a magnitude.
    - The Moon is NOT combustible here. A Moon near the Sun IS a dark/new Moon,
      which the tithi engine already penalises (tithis 1-3). Combustion covers
      venus/jupiter/mercury/mars/saturn only.
    - Items marked  # >>> REVIEW  are values you have not finalised. They have
      sensible defaults so the engine runs, but they are the ones to confirm.

INPUT CONTRACT
    chart = {
        "sun":  {"rasi": "mesha", "degree": 5.4, "house": 1},   # degree ABSOLUTE 0-360
        "moon": {"rasi": "tula",  "degree": 200.1, "house": 7},
        ...one entry per planet in PLANETS...
    }
    'house' is 1-12 with house 1 = the ascendant sign.

Run `python core/point_scoring.py` for a worked sample.
"""

from utils.constant import (
    PLANET_EXALTATION,
    PLANET_DEBILITATION,
    PLANET_OWN_HOUSES,
    PLANET_RELATIONSHIPS,
    RASI_TO_DEGREE,
    PLANETS,
)
from utils.calculations.utils import (
    calculate_degree_difference,
)
from utils.calculations.tithi import (
    describe as describe_tithi,
    benefic_weight as tithi_benefic_weight,
)

# ==========================================================================
# THE ONE CONFIG BLOCK - tune every number here
# ==========================================================================
POINTS = {

    # --- Track 2: sign dignity ladder (pick the single best; mutually
    # exclusive because a planet sits in exactly one rasi) -----------------
    "dignity": {
        "neecha_bhanga": 120,   # debilitation cancelled -> raja yoga
        "exalted":       100,
        "moolatrikona":   80,
        "own":            60,
        "friend":         30,
        "neutral":        25,
        "enemy":          15,
        "debilitated":    10,
    },
    "dig_bala": 50,             # added ON TOP of dignity when directionally strong
    "track2_cap": 200,         # Track 2 (dignity + dig) is capped here

    # Moolatrikona degree bands (IN-SIGN degrees). MT is a sub-range of an own
    # sign; a planet in its own sign AND inside this band scores 80 instead of
    # 60. Exaltation is sign-wide here, so MT signs that coincide with the
    # exaltation sign (Mercury/Moon) are naturally subsumed by exalted=100.
    # >>> REVIEW  standard classical ranges; confirm if you use different ones.
    "moolatrikona_range": {
        "sun":     ("simha",   0, 20),
        "mars":    ("mesha",   0, 12),
        "jupiter": ("dhanu",   0, 10),
        "venus":   ("tula",    0, 15),
        "saturn":  ("kumbha",  0, 20),
    },

    # Dig bala house per planet (full directional strength).
    "dig_bala_house": {
        "jupiter": 1, "mercury": 1,    # East / Lagna
        "sun": 10, "mars": 10,         # South / 10th
        "saturn": 7,                   # West / 7th
        "moon": 4, "venus": 4,         # North / 4th
    },

    # --- Track 1: contact base points ------------------------------------
    # Redeemers (benefic contacts add). Mercury is intentionally NOT a redeemer
    # here - it was not in your 100/80/60/25 list. Add "mercury": N to include.
    "redeemer_base": {
        "jupiter": 80,
        "venus":   60,
        # moon is handled by tithi (25 at the band edge -> 100 at purnima)
    },
    # Afflicters (malefic contacts subtract). No per-planet segregation: one
    # base of 60, then shaped by the aspect-power table below.
    "afflicter_base": {
        "saturn": 60, "mars": 60, "rahu": 60, "ketu": 60,
    },

    # Malefic pairs that do NOT afflict each other WHEN CONJUNCT -> their
    # conjunction is not counted as papathuvam. Ketu takes on the nature of the
    # malefic it joins, so Saturn+Ketu / Mars+Ketu cancel their mutual affliction
    # when together. A distant Saturn/Mars ASPECT onto Ketu still counts.
    "papathuvam_exempt_pairs": [
        frozenset({"saturn", "ketu"}),
        frozenset({"mars", "ketu"}),
    ],

    # Aspect power by aspect-house-distance (applies to BOTH benefic and
    # malefic aspects). Every planet has the 7th; specials add their own.
    "aspect_power": {
        "saturn":  {3: 0.25, 7: 1.00, 10: 0.75},
        "jupiter": {5: 0.50, 7: 1.00, 9: 0.75},
        "mars":    {4: 0.50, 7: 1.00, 8: 0.25},
        "_default": {7: 1.00},
    },

    # Conjunction tightness by orb (angular separation between the two planets).
    # The closer they sit, the fuller the contact; past ~22deg it is not a
    # conjunction. Bands: (max_orb_deg, multiplier).
    "conjunction_tightness": [
        (6.0,  1.00),   # 0-6   deg : very close  -> full
        (13.0, 0.70),   # 6-13  deg
        (18.0, 0.30),   # 13-18 deg
        (22.0, 0.10),   # 18-22 deg
        (30.0, 0.00),   # 22-30 deg : too wide    -> not conjunct
    ],

    # Aspect SHARPNESS by in-sign degree orb. A house-based aspect is exact when
    # the aspecting and aspected planets share the same degree WITHIN their signs
    # (e.g. both at 28deg -> bang on, full value). As that in-sign gap widens the
    # aspect fades and eventually is not cast at all:
    #     Saturn@28 -> Jupiter@28  -> orb 0   -> sharp   (full)
    #     Saturn@28 -> Jupiter@7   -> orb 21  -> out of orb (ignored)
    # This MULTIPLIES the aspect_power above. Conjunctions are unaffected - they
    # carry their own orb via conjunction_tightness. Bands: (max_orb, mult, label)
    "aspect_sharpness": [
        (5.0,  1.00, "sharp"),
        (10.0, 0.50, "average"),
        (15.0, 0.25, "low"),
    ],

    # Combustion: fixed 0-5 deg = -70; the rest of the planet's orb splits in
    # half -> first half -40, second half -20. Moon excluded by design.
    # NOTE: these orbs are the classically correct ones. constant.COMBUST_DEGREES
    # currently has mars/saturn SWAPPED (mars:15, saturn:17) - a latent bug.
    "combust_orb": {
        "venus": 9, "jupiter": 11, "mercury": 13, "saturn": 15, "mars": 17,
    },
    "combust_deep": -70,       # 0-5 deg
    "combust_first_half": -40,
    "combust_second_half": -20,

    # Full-Moon 6th/8th bonus: when the Moon is full (tithi 13-15), any of these
    # planets sitting in the 6th or 8th house FROM the Moon gets a flat bonus.
    "full_moon_6_8_bonus": 30,
    "full_moon_6_8_planets": {"jupiter", "venus", "mercury", "mars", "saturn"},

    # Dark-Moon conjunction penalty by tithi (the Moon is the afflicter).
    "dark_moon_penalty": {1: -60, 2: -45, 3: -30},

    # Full-Moon plateau: tithis 13/14/15 all score the max 100 (mode B). Set to
    # False for the smooth tent (13->85, 14->92.5, 15->100).
    "full_moon_plateau": True,

    # --- Collapse the two tracks into ONE 0-10 planet strength ------------
    # Needed only by the prediction engines (dasha favourability, profession)
    # that consume a single number. Placement (Sthana/Dig, 0-200) sets the
    # base; the net contact balance (subathuvam+papathuvam) nudges it up/down.
    # This maps back onto the SAME 0-10 / -5..15 scale the old final_score used,
    # so the existing thresholds stay valid -> predictions re-base without a
    # rule rewrite. >>> REVIEW  weights/spans are sensible defaults; tune here.
    "strength_map": {
        "sthana_full":      200.0,   # sthana that reads as full placement
        "contact_full":     200.0,   # net contacts that read as a full +/- swing
        "placement_weight": 0.6,     # how much Sthana/Dig drives the number
        "contact_weight":   0.4,     # how much the net contact balance drives it
    },
}

# The luminaries/nodes that do not participate as generic afflicter contacts.
# The Sun's only Track-1 effect on others is combustion.
_NON_CONTACT_SUN = "sun"

# --------------------------------------------------------------------------
# Derived lookups
# --------------------------------------------------------------------------
RASI_LORD = {}
for _p, _signs in PLANET_OWN_HOUSES.items():
    for _s in _signs:
        RASI_LORD[_s] = _p

# sign that each planet is exalted in -> used for neecha bhanga condition 2
EXALTED_IN_SIGN = {sign: planet for planet, sign in PLANET_EXALTATION.items()}

KENDRA_HOUSES = {1, 4, 7, 10}


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def _in_sign_degree(abs_degree):
    """Degree within the current sign, 0-30."""
    return float(abs_degree) % 30.0


def _house_distance(from_house, to_house):
    """1-12: which house `to_house` is, counted from `from_house`.
    Same house = 1, opposite = 7."""
    return ((int(to_house) - int(from_house)) % 12) + 1


def _ordinal(n):
    """1 -> '1st', 2 -> '2nd', 3 -> '3rd', 7 -> '7th' ... (nicer fact labels)."""
    n = int(n)
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _aspect_sharpness(source_abs_deg, target_abs_deg):
    """How exact a house-based aspect is, from the in-sign degree gap between the
    aspecting and aspected planets (exact when their in-sign degrees match).
    Returns (multiplier, orb_deg, label); beyond the last band -> multiplier 0."""
    orb = abs(_in_sign_degree(source_abs_deg) - _in_sign_degree(target_abs_deg))
    for max_orb, mult, label in POINTS["aspect_sharpness"]:
        if orb <= max_orb:
            return mult, orb, label
    return 0.0, orb, "out of orb"


def _conjunction_tightness(deg_a, deg_b):
    """Conjunction strength from the angular separation between two planets.
    Returns (multiplier, orb_deg); beyond the last band -> multiplier 0."""
    orb = calculate_degree_difference(float(deg_a), float(deg_b))
    for max_orb, mult in POINTS["conjunction_tightness"]:
        if orb <= max_orb:
            return mult, orb
    return 0.0, orb


def _relationship(planet, other):
    """natural relationship of `planet` toward `other`: friend/enemy/neutral."""
    rel = PLANET_RELATIONSHIPS.get(planet, {})
    if other in rel.get("friend", []):
        return "friend"
    if other in rel.get("enemy", []):
        return "enemy"
    return "neutral"


def _aspect_power(source_planet, dist):
    """Power with which `source_planet` casts an aspect at house-distance `dist`.
    0.0 means no aspect at that distance."""
    if source_planet in ("rahu", "ketu"):
        return 0.0          # nodes cast no aspects; they afflict by conjunction only
    table = POINTS["aspect_power"].get(source_planet, POINTS["aspect_power"]["_default"])
    return table.get(dist, 0.0)


# --------------------------------------------------------------------------
# Track 2 - dignity + dig bala
# --------------------------------------------------------------------------
def _neecha_bhanga(chart, planet):
    """Simplified Neecha Bhanga Raja Yoga detector.

    >>> REVIEW  NBRY has many classical variants; this implements a common
    subset. Confirm which conditions you want. A debilitated planet's fall is
    treated as cancelled if ANY holds:
       (1) the lord of the debilitation sign is in a kendra (1/4/7/10) from
           the Lagna OR from the Moon;
       (2) the planet exalted in that same sign is in a kendra from Lagna/Moon;
       (3) the dispositor (sign lord) is itself exalted;
       (4) planet and dispositor are in mutual sign exchange (parivartana).
    Returns (is_cancelled: bool, reason: str|None).
    """
    cd = chart.get(planet) or {}
    rasi = cd.get("rasi")
    if not rasi or PLANET_DEBILITATION.get(planet) != rasi:
        return False, None

    moon_house = (chart.get("moon") or {}).get("house")

    def in_kendra_from_lagna_or_moon(p):
        ph = (chart.get(p) or {}).get("house")
        if ph is None:
            return False
        if ph in KENDRA_HOUSES:
            return True
        if moon_house is not None and _house_distance(moon_house, ph) in KENDRA_HOUSES:
            return True
        return False

    dispositor = RASI_LORD.get(rasi)

    # (1) lord of the debilitation sign in a kendra
    if dispositor and in_kendra_from_lagna_or_moon(dispositor):
        return True, f"dispositor {dispositor} in kendra (from Lagna/Moon)"

    # (2) the planet exalted in this sign is in a kendra
    exalter = EXALTED_IN_SIGN.get(rasi)
    if exalter and in_kendra_from_lagna_or_moon(exalter):
        return True, f"{exalter} (exalted in {rasi}) in kendra"

    # (3) dispositor exalted
    if dispositor:
        disp_rasi = (chart.get(dispositor) or {}).get("rasi")
        if disp_rasi and PLANET_EXALTATION.get(dispositor) == disp_rasi:
            return True, f"dispositor {dispositor} is exalted"

    # (4) mutual exchange between planet and dispositor
    if dispositor:
        disp_rasi = (chart.get(dispositor) or {}).get("rasi")
        if disp_rasi in PLANET_OWN_HOUSES.get(planet, []):
            return True, f"exchange with dispositor {dispositor}"

    return False, None


def _dignity(chart, planet):
    """(label, points) for the planet's single best sign dignity."""
    cd = chart.get(planet) or {}
    rasi = cd.get("rasi")
    d = POINTS["dignity"]

    # Nodes have no classical sign dignity in this dataset.
    if planet in ("rahu", "ketu") or not rasi:
        return "none", 0

    # Neecha bhanga outranks even exaltation.
    cancelled, why = _neecha_bhanga(chart, planet)
    if cancelled:
        return f"neecha_bhanga ({why})", d["neecha_bhanga"]

    if PLANET_EXALTATION.get(planet) == rasi:
        return "exalted", d["exalted"]
    if PLANET_DEBILITATION.get(planet) == rasi:
        return "debilitated", d["debilitated"]

    own_signs = PLANET_OWN_HOUSES.get(planet, [])
    if rasi in own_signs:
        mt = POINTS["moolatrikona_range"].get(planet)
        if mt and mt[0] == rasi and mt[1] <= _in_sign_degree(cd.get("degree", 0)) < mt[2]:
            return "moolatrikona", d["moolatrikona"]
        return "own", d["own"]

    # Otherwise: relationship to the sign lord.
    lord = RASI_LORD.get(rasi)
    if lord and lord != planet:
        rel = _relationship(planet, lord)
        return rel, d[rel]
    return "neutral", d["neutral"]


def _track2_sthana_dig(chart, planet):
    label, dignity_pts = _dignity(chart, planet)
    # `label` may carry a parenthetical (e.g. neecha_bhanga reason); keep the
    # bare tier name for the UI chip.
    tier = label.split(" (")[0]
    facts = [(f"dignity: {label}", dignity_pts)]
    total = dignity_pts

    has_dig = False
    dig_house = POINTS["dig_bala_house"].get(planet)
    if dig_house is not None and (chart.get(planet) or {}).get("house") == dig_house:
        facts.append((f"dig bala (house {dig_house})", POINTS["dig_bala"]))
        total += POINTS["dig_bala"]
        has_dig = True

    total = min(total, POINTS["track2_cap"])
    return round(total, 1), facts, {"dignity": tier, "dig_bala": has_dig}


# --------------------------------------------------------------------------
# Track 1 - contacts, combustion, tithi Moon
# --------------------------------------------------------------------------
def _moon_benefic_points(tithi_sheet):
    """The Moon's redeemer points, 25 (band edge) -> 100 (purnima)."""
    if POINTS["full_moon_plateau"] and tithi_sheet.get("is_full_moon"):
        return 100.0
    t = tithi_sheet["tithi"]
    bw = tithi_benefic_weight(t)            # 0.0 outside band, else 0.5-2.0 tent
    if bw <= 0:
        return 0.0
    return round(25.0 + (bw - 0.5) / 1.5 * 75.0, 1)


def _combustion(chart, planet):
    """Combustion penalty for `planet` (0 if not combustible / not combust)."""
    orb = POINTS["combust_orb"].get(planet)
    if orb is None:
        return 0, None
    sun = chart.get("sun")
    if not sun:
        return 0, None
    dist = calculate_degree_difference(
        float((chart[planet] or {}).get("degree", 0)), float(sun.get("degree", 0))
    )
    if dist > orb:
        return 0, None
    if dist <= 5:
        return POINTS["combust_deep"], f"deep combust ({dist:.1f}deg from Sun)"
    midpoint = 5 + (orb - 5) / 2.0
    if dist <= midpoint:
        return POINTS["combust_first_half"], f"combust, first half ({dist:.1f}deg)"
    return POINTS["combust_second_half"], f"combust, second half ({dist:.1f}deg)"


def _track1_contacts(chart, planet):
    """Benefic + malefic contacts, combustion, tithi Moon, full-moon 6/8 bonus."""
    facts = []
    total = 0.0
    cd = chart.get(planet) or {}
    my_house = cd.get("house")

    # tithi fact sheet for the chart (needs Sun + Moon absolute degrees)
    sun_deg = (chart.get("sun") or {}).get("degree")
    moon_deg = (chart.get("moon") or {}).get("degree")
    tithi_sheet = None
    if sun_deg is not None and moon_deg is not None:
        tithi_sheet = describe_tithi(float(sun_deg), float(moon_deg))

    for other in PLANETS:
        if other == planet or other == _NON_CONTACT_SUN or other not in chart:
            continue
        oh = (chart[other] or {}).get("house")
        if oh is None or my_house is None:
            continue

        tightness, conj_orb = _conjunction_tightness(
            cd.get("degree", 0), (chart[other] or {}).get("degree", 0)
        )
        is_conj = tightness > 0

        dist = _house_distance(oh, my_house)          # how `other` sees `planet`
        apower = _aspect_power(other, dist)
        # Fade the aspect by the in-sign degree gap: exact (equal degree) = full,
        # widening gap = weaker, beyond ~15deg = not cast.
        sharp_mult, sharp_orb, sharp_label = _aspect_sharpness(
            (chart[other] or {}).get("degree", 0), cd.get("degree", 0)
        )
        eff_apower = apower * sharp_mult
        is_aspect = eff_apower > 0 and dist != 1

        # ---- Moon: tithi-driven -----------------------------------------
        if other == "moon" and tithi_sheet is not None:
            # dark Moon afflicts a CONJUNCT planet
            dark = POINTS["dark_moon_penalty"].get(tithi_sheet["tithi"])
            if dark and is_conj:
                facts.append((f"dark Moon conj ({tithi_sheet['tithi_name']})", dark))
                total += dark
                continue
            mpts = _moon_benefic_points(tithi_sheet)
            if mpts > 0:
                if is_conj:
                    c = round(mpts * tightness, 1)
                    facts.append((f"Moon conj ({tithi_sheet['tithi_name']})", c))
                    total += c
                elif is_aspect and tithi_sheet.get("aspect_power", 0) > 0:
                    # crescent Moon has no aspect power (no light) -> gated, and
                    # faded further by the in-sign degree gap (sharp_mult)
                    c = round(mpts * tithi_sheet["aspect_power"] * sharp_mult, 1)
                    facts.append((f"Moon {_ordinal(dist)} aspect "
                                  f"({tithi_sheet['tithi_name']}, {sharp_label})", c))
                    total += c
            continue

        # ---- Redeemers (Jupiter, Venus) ---------------------------------
        if other in POINTS["redeemer_base"]:
            base = POINTS["redeemer_base"][other]
            if is_conj:
                c = round(base * tightness, 1)
                facts.append((f"{other} conj (+)", c)); total += c
            elif is_aspect:
                c = round(base * eff_apower, 1)
                facts.append((f"{other} {_ordinal(dist)} aspect {sharp_label} (+)", c))
                total += c
            continue

        # ---- Afflicters (Saturn, Mars, Rahu, Ketu) ----------------------
        if other in POINTS["afflicter_base"]:
            base = POINTS["afflicter_base"][other]
            exempt = frozenset({planet, other}) in POINTS["papathuvam_exempt_pairs"]
            if is_conj:
                # exempt pairs (Saturn+Ketu, Mars+Ketu) don't afflict when
                # TOGETHER; a distant aspect below still counts.
                if exempt:
                    continue
                c = -round(base * tightness, 1)
                facts.append((f"{other} conj (-)", c)); total += c
            elif is_aspect:
                c = -round(base * eff_apower, 1)
                facts.append((f"{other} {_ordinal(dist)} aspect {sharp_label} (-)", c))
                total += c
            continue

    # ---- combustion --------------------------------------------------
    cpts, creason = _combustion(chart, planet)
    if cpts:
        facts.append((creason, cpts)); total += cpts

    # ---- full-Moon 6th/8th bonus -------------------------------------
    if (tithi_sheet and tithi_sheet.get("is_full_moon")
            and planet in POINTS["full_moon_6_8_planets"]):
        moon_house = (chart.get("moon") or {}).get("house")
        if moon_house is not None and my_house is not None:
            if _house_distance(moon_house, my_house) in (6, 8):
                b = POINTS["full_moon_6_8_bonus"]
                facts.append(("full Moon 6th/8th bonus", b)); total += b

    # Split the contacts into two separate scores instead of one net sum:
    #   subathuvam = every benefic (positive) contribution
    #   papathuvam = every malefic (negative) contribution  (kept negative)
    subathuvam = round(sum(p for _, p in facts if p > 0), 1)
    papathuvam = round(sum(p for _, p in facts if p < 0), 1)
    return round(total, 1), subathuvam, papathuvam, facts


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------
def _facts_to_dicts(facts):
    """[(note, pts)] -> [{"note":..., "value":...}] for JSON payloads."""
    return [{"note": n, "value": p} for n, p in facts]


def score_planet(chart, planet):
    t1, sub1, pap1, f1 = _track1_contacts(chart, planet)
    t2, f2, meta2 = _track2_sthana_dig(chart, planet)
    return {
        "planet": planet,
        "tracks": {
            # Track 1: benefic (subathuvam) and malefic (papathuvam) contacts
            # kept as TWO separate scores; `value` is the net kept for reference.
            "subathuvam_papathuvam": {
                "value": t1,
                "subathuvam": sub1,
                "papathuvam": pap1,
                "facts": _facts_to_dicts(f1),
            },
            # Track 2: placement strength 0-200 with the dignity tier for the chip.
            "dig_sthana": {
                "value": t2,
                "dignity": meta2["dignity"],
                "dig_bala": meta2["dig_bala"],
                "facts": _facts_to_dicts(f2),
            },
        },
    }


def score_chart(chart):
    """Score every planet present in `chart`."""
    return {p: score_planet(chart, p) for p in PLANETS if p in chart}


# --- single-number collapse (for the prediction engines) ------------------
def _clamp01(x):
    return max(0.0, min(1.0, x))


def contact_net(result):
    """Net contact balance (subathuvam + papathuvam) for a scored planet."""
    t1 = result["tracks"]["subathuvam_papathuvam"]
    return round(t1.get("subathuvam", 0) + t1.get("papathuvam", 0), 1)


def planet_strength_0_10(result):
    """Collapse a scored planet's two tracks into one 0-10 strength."""
    m = POINTS["strength_map"]
    sthana = result["tracks"]["dig_sthana"]["value"]
    net = contact_net(result)
    placement = _clamp01(sthana / m["sthana_full"])              # 0..1
    contact = _clamp01(0.5 + net / (2.0 * m["contact_full"]))    # 0..1 (0.5 = neutral)
    s01 = m["placement_weight"] * placement + m["contact_weight"] * contact
    return round(s01 * 10.0, 2)


def planet_strength_legacy(result):
    """The 0-10 strength mapped onto the legacy -5..15 scale, so old thresholds
    (final_score > 5, ChartQuery.strength, etc.) keep working unchanged."""
    return round(planet_strength_0_10(result) * 2.0 - 5.0, 2)


# --------------------------------------------------------------------------
# self-test: `python core/point_scoring.py`
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # A hand-built sample chart (absolute degrees). Ascendant = mesha (house 1).
    sample = {
        "sun":     {"rasi": "mesha",      "degree": 8.0,   "house": 1},   # exalted
        "moon":    {"rasi": "vrishabha",  "degree": 45.0,  "house": 2},   # tithi ~ from sun
        "mars":    {"rasi": "makara",     "degree": 278.0, "house": 10},  # exalted + dig(10)
        "mercury": {"rasi": "mesha",      "degree": 3.0,   "house": 1},   # combust (near sun)
        "jupiter": {"rasi": "karka",      "degree": 100.0, "house": 4},   # exalted, trikona? h4=kendra
        "venus":   {"rasi": "kanya",      "degree": 165.0, "house": 6},   # debilitated
        "saturn":  {"rasi": "tula",       "degree": 200.0, "house": 7},   # exalted + dig(7)
        "rahu":    {"rasi": "mithuna",    "degree": 75.0,  "house": 3},
        "ketu":    {"rasi": "dhanu",      "degree": 255.0, "house": 9},
    }
    ts = describe_tithi(sample["sun"]["degree"], sample["moon"]["degree"])
    print(f"Moon: {ts['tithi_name']} (tithi {ts['tithi']}), "
          f"full={ts['is_full_moon']}, illum={ts['illumination']}\n")

    for planet, res in score_chart(sample).items():
        t1 = res["tracks"]["subathuvam_papathuvam"]
        t2 = res["tracks"]["dig_sthana"]
        print(f"{planet.upper():9s}  suba={t1['subathuvam']:+6.1f} papa={t1['papathuvam']:+6.1f}   "
              f"T2(sthana/dig)={t2['value']:6.1f}  [{t2['dignity']}"
              f"{' +dig' if t2['dig_bala'] else ''}]")
        for f in t1["facts"] + t2["facts"]:
            print(f"            {f['value']:+7.1f}  {f['note']}")
        print()
