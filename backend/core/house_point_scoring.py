"""
House-level point-scale scoring - the house counterpart of core.point_scoring.
================================================================================

WHY THIS EXISTS
    The planet point model scores planets only. House-driven views (house cards,
    the house Heat Map / Table, and the house rows inside marriage/relationship
    and profession) still ran on the flat legacy final_score. This module scores
    houses on the SAME point scale and reuses the SAME tunables (base values,
    aspect-power tables, tithi Moon) from core.point_scoring - there is still one
    config block for magnitudes; this file only adds house-specific structure.

THE MODEL (one track only)
    Subathuvam / Papathuvam  - CONTACTS on the house: benefic vs malefic
        OCCUPANTS (a planet sitting in the house = full contact) and ASPECTS
        (planet -> house by house-distance, scaled by the aspect-power table).
        The Moon is tithi-driven. Split into two separate scores.

    A house is scored purely by which planets sit in / aspect it. There is NO
    Sthana balam (lord dignity) and NO parivarthanai here - those belong to the
    PLANET model. So a house has a single track (unlike a planet's two).

SINGLE-NUMBER COLLAPSE (for predictions / legacy views)
    house_strength = the net contact balance mapped onto the same 0-10 / -5..15
    scale planets use, so dasha favourability, profession and marriage
    thresholds stay valid.

INPUT CONTRACT
    chart            {planet: {"rasi","house","degree"(abs)}}  (same as planets)
    ascendant_rasi   e.g. "mesha"  (house 1's sign)
"""

from utils.constant import PLANETS, RASI_TO_DEGREE
from utils.calculations.tithi import describe as describe_tithi
from core.point_scoring import (
    POINTS,
    _house_distance,
    _aspect_power,
    _ordinal,
    _clamp01,
    _moon_benefic_points,
)

# ==========================================================================
# House-specific config. Magnitudes (base points, aspect power, tithi) are
# INHERITED from core.point_scoring.POINTS; only the collapse span is new.
# ==========================================================================
HOUSE_POINTS = {
    "contact_full": POINTS["strength_map"]["contact_full"],  # net -> full +/- swing
}


# --------------------------------------------------------------------------
def _house_rasi_map(ascendant_rasi):
    """{house_num: rasi} counting signs forward from the ascendant."""
    rasi_list = list(RASI_TO_DEGREE.keys())
    if ascendant_rasi not in rasi_list:
        return {}
    asc = rasi_list.index(ascendant_rasi)
    return {h: rasi_list[(asc + h - 1) % 12] for h in range(1, 13)}


def _house_track1(house_num, chart, tithi_sheet):
    """Benefic + malefic contacts on a house (occupants + aspects, tithi Moon).
    Returns (net, subathuvam, papathuvam, facts)."""
    facts = []
    for other in PLANETS:
        # Sun is neutral as an occupant/aspect here (its only planet-side Track-1
        # role is combustion, which does not apply to a house).
        if other not in chart or other == "sun":
            continue
        oh = (chart[other] or {}).get("house")
        if oh is None:
            continue

        is_occupant = (oh == house_num)
        dist = _house_distance(oh, house_num)     # how `other` aspects this house
        apower = _aspect_power(other, dist)
        is_aspect = apower > 0 and dist != 1      # dist 1 = same house = occupant

        # ---- Moon: tithi-driven ----------------------------------------
        if other == "moon" and tithi_sheet is not None:
            dark = POINTS["dark_moon_penalty"].get(tithi_sheet["tithi"])
            if is_occupant:
                if dark:
                    facts.append((f"dark Moon in house ({tithi_sheet['tithi_name']})", dark))
                else:
                    m = _moon_benefic_points(tithi_sheet)
                    if m > 0:
                        facts.append((f"Moon in house ({tithi_sheet['tithi_name']})", round(m, 1)))
            elif is_aspect and tithi_sheet.get("aspect_power", 0) > 0:
                m = _moon_benefic_points(tithi_sheet)
                if m > 0:
                    c = round(m * tithi_sheet["aspect_power"], 1)
                    facts.append((f"Moon {_ordinal(dist)} aspect ({tithi_sheet['tithi_name']})", c))
            continue

        # ---- Redeemers (Jupiter, Venus) --------------------------------
        if other in POINTS["redeemer_base"]:
            base = POINTS["redeemer_base"][other]
            if is_occupant:
                facts.append((f"{other} in house (+)", base))
            elif is_aspect:
                facts.append((f"{other} {_ordinal(dist)} aspect (+)", round(base * apower, 1)))
            continue

        # ---- Afflicters (Saturn, Mars, Rahu, Ketu) ---------------------
        if other in POINTS["afflicter_base"]:
            base = POINTS["afflicter_base"][other]
            if is_occupant:
                facts.append((f"{other} in house (-)", -base))
            elif is_aspect:
                facts.append((f"{other} {_ordinal(dist)} aspect (-)", -round(base * apower, 1)))
            continue

    subathuvam = round(sum(p for _, p in facts if p > 0), 1)
    papathuvam = round(sum(p for _, p in facts if p < 0), 1)
    net = round(subathuvam + papathuvam, 1)
    return net, subathuvam, papathuvam, facts


def score_house(house_num, house_rasi, chart, tithi_sheet):
    """Single-track (Subathuvam / Papathuvam) score for one house."""
    net, sub, pap, facts = _house_track1(house_num, chart, tithi_sheet)
    return {
        "house": house_num,
        "rasi": house_rasi,
        "tracks": {
            "subathuvam_papathuvam": {
                "value": net,
                "subathuvam": sub,
                "papathuvam": pap,
                "facts": [{"note": n, "value": p} for n, p in facts],
            },
        },
    }


def score_houses(chart, ascendant_rasi):
    """Score all 12 houses (contacts only)."""
    hmap = _house_rasi_map(ascendant_rasi)
    if not hmap:
        return {}
    sun = (chart.get("sun") or {}).get("degree")
    moon = (chart.get("moon") or {}).get("degree")
    tithi_sheet = None
    if sun is not None and moon is not None:
        tithi_sheet = describe_tithi(float(sun), float(moon))
    return {h: score_house(h, hmap[h], chart, tithi_sheet) for h in range(1, 13)}


# --- single-number collapse (net contact only) ----------------------------
def house_strength_0_10(house_result):
    """Collapse a house into one 0-10 strength from its net contact balance
    (0.5 -> neutral). No lord/Sthana component."""
    net = house_result["tracks"]["subathuvam_papathuvam"]["value"]
    return round(_clamp01(0.5 + net / (2.0 * HOUSE_POINTS["contact_full"])) * 10.0, 2)


def house_strength_legacy(house_result):
    """0-10 house strength mapped onto the legacy -5..15 scale, so existing
    thresholds (house >= 6, ChartQuery.strength, marriage colours) stay valid."""
    return round(house_strength_0_10(house_result) * 2.0 - 5.0, 2)


# --------------------------------------------------------------------------
# self-test: `python core/house_point_scoring.py`
# --------------------------------------------------------------------------
if __name__ == "__main__":
    from core.point_scoring import score_chart

    sample = {
        "sun":     {"rasi": "mesha",      "degree": 8.0,   "house": 1},
        "moon":    {"rasi": "vrishabha",  "degree": 45.0,  "house": 2},
        "mars":    {"rasi": "makara",     "degree": 278.0, "house": 10},
        "mercury": {"rasi": "mesha",      "degree": 3.0,   "house": 1},
        "jupiter": {"rasi": "karka",      "degree": 100.0, "house": 4},
        "venus":   {"rasi": "kanya",      "degree": 165.0, "house": 6},
        "saturn":  {"rasi": "tula",       "degree": 200.0, "house": 7},
        "rahu":    {"rasi": "mithuna",    "degree": 75.0,  "house": 3},
        "ketu":    {"rasi": "dhanu",      "degree": 255.0, "house": 9},
    }
    score_chart(sample)  # (planets not needed for house scoring anymore)
    houses = score_houses(sample, "mesha")
    for h, res in houses.items():
        t1 = res["tracks"]["subathuvam_papathuvam"]
        strength = house_strength_legacy(res)
        print(f"H{h:2d} {res['rasi']:10s} "
              f"suba={t1['subathuvam']:+6.1f} papa={t1['papathuvam']:+6.1f} "
              f"strength={strength:6.2f}")
        for f in t1["facts"]:
            print(f"        {f['value']:+7.1f}  {f['note']}")
