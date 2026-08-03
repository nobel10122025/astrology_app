"""
Tithi engine - the Moon's phase, and what it does to the planets it touches.

WHY THIS EXISTS
    The old Moon logic (utils.calculate_moon_position_effect) measured the
    Sun-Moon gap with `calculate_degree_difference`, which returns the MINIMUM
    separation (0-180). That makes a Moon 60deg ahead of the Sun (shukla
    panchami - growing, benefic) numerically identical to one 300deg ahead
    (krishna, dying). Paksha was therefore invisible to the whole engine.

    Tithi needs the SIGNED separation:  (moon - sun) mod 360.

THE RULE SET (as stated by the user)
    - Shukla panchami (tithi 5) -> Krishna dashami (tithi 25) is the benefic
      band. The Moon grows to full at purnima (tithi 15), then its benefic
      power reduces again until krishna dashami.
    - The remaining ~10 tithis (26 -> 4) are not good.
        * tithi 4 (shukla chaturthi) is average
        * tithi 1-3 are BAD for any planet conjunct the Moon
        * tithi 26-30 (the dark run into amavasya) is likewise not benefic
    - A crescent Moon HAS NO ASPECT POWER, because it has no light. It can
      still affect a planet it is conjunct with - light is needed to cast a
      drishti, not to sit in the same house.

Everything here is pure arithmetic on two absolute degrees; no chart context
needed, so it is trivially testable.
"""

import math

# --- tithi bands ----------------------------------------------------------
DEGREES_PER_TITHI = 12.0          # 360 / 30
TITHIS_PER_PAKSHA = 15

MOON_BENEFIC_START = 5            # shukla panchami - benefic band opens
MOON_BENEFIC_PEAK = 15            # purnima - full moon, maximum benefic power
MOON_BENEFIC_END = 25             # krishna dashami - benefic band closes

MOON_AVERAGE_TITHIS = {4}         # shukla chaturthi - neither helps nor harms
MOON_MALEFIC_TITHIS = {1, 2, 3}   # just after amavasya - harms a conjunct planet

# "Full moon (last 3 days)" - the top-ranked benefic influence (see
# core.strength_tracks REDEEMER_WEIGHT).
FULL_MOON_TITHIS = {13, 14, 15}

# ...plus a luminosity catch. The instant of exact fullness is the BOUNDARY
# between tithi 15 and 16, so a Moon at 180.1deg separation is 100% lit but
# indexes as krishna pratipada and would miss the tithi test above. Anything
# this bright is treated as a full Moon regardless of index. Raise toward 1.0
# to follow the tithi numbering strictly.
FULL_MOON_ILLUMINATION = 0.97

# The dark run into amavasya. The user described tithis 26-30 as "not good"
# without calling them actively bad, so they contribute NOTHING rather than a
# penalty. Raise this to make them afflict a conjunct planet like tithi 1-3.
DARK_TAIL_MALEFIC_WEIGHT = 0.0

# Benefic contribution at the edges of the band vs at purnima. Kept on the
# 0.5 - 2.0 scale the existing scoring engine already uses for Moon effects.
BENEFIC_WEIGHT_MIN = 0.5
BENEFIC_WEIGHT_MAX = 2.0

# How hard tithi 1-3 hits a conjunct planet (tithi 1 is darkest, so worst).
MALEFIC_WEIGHT_BY_TITHI = {1: 1.0, 2: 0.75, 3: 0.5}

# Below this illumination the Moon casts no usable drishti at all.
ASPECT_LIGHT_FLOOR = 0.15

TITHI_NAMES = [
    "pratipada", "dwitiya", "tritiya", "chaturthi", "panchami", "shashthi",
    "saptami", "ashtami", "navami", "dashami", "ekadashi", "dwadashi",
    "trayodashi", "chaturdashi", "purnima",
]


def separation(sun_degree, moon_degree):
    """SIGNED Sun->Moon separation in [0, 360). This is the number the old
    code could not see - it is what distinguishes waxing from waning."""
    return (moon_degree - sun_degree) % 360.0


def tithi_number(sun_degree, moon_degree):
    """Tithi index 1-30. 1-15 = shukla (waxing), 16-30 = krishna (waning).
    15 = purnima (full moon), 30 = amavasya (new moon)."""
    return int(separation(sun_degree, moon_degree) // DEGREES_PER_TITHI) + 1


def illumination(sun_degree, moon_degree):
    """Fraction of the Moon's disc that is lit, 0.0 (amavasya) - 1.0 (purnima).
    The physical quantity: (1 - cos(separation)) / 2."""
    sep = math.radians(separation(sun_degree, moon_degree))
    return (1.0 - math.cos(sep)) / 2.0


def classify(tithi):
    """The user's four bands.

    Returns one of:
        "benefic"  - tithi 5-25, helps whatever it touches
        "average"  - tithi 4, neutral
        "malefic"  - tithi 1-3, harms a CONJUNCT planet
        "dark"     - tithi 26-30, gives nothing
    """
    if MOON_BENEFIC_START <= tithi <= MOON_BENEFIC_END:
        return "benefic"
    if tithi in MOON_AVERAGE_TITHIS:
        return "average"
    if tithi in MOON_MALEFIC_TITHIS:
        return "malefic"
    return "dark"


def benefic_weight(tithi):
    """How much good the Moon does, as a tent function peaking at purnima.

    Grows 5 -> 15, then reduces 15 -> 25, exactly as described: "moon will grow
    till full moon and again reduce till dashami". Zero outside the band.
    """
    if classify(tithi) != "benefic":
        return 0.0
    span = BENEFIC_WEIGHT_MAX - BENEFIC_WEIGHT_MIN
    if tithi <= MOON_BENEFIC_PEAK:
        frac = (tithi - MOON_BENEFIC_START) / (MOON_BENEFIC_PEAK - MOON_BENEFIC_START)
    else:
        frac = (MOON_BENEFIC_END - tithi) / (MOON_BENEFIC_END - MOON_BENEFIC_PEAK)
    return round(BENEFIC_WEIGHT_MIN + span * frac, 3)


def malefic_weight(tithi):
    """How much harm a dark Moon does to a planet it is CONJUNCT with."""
    if tithi in MALEFIC_WEIGHT_BY_TITHI:
        return MALEFIC_WEIGHT_BY_TITHI[tithi]
    if classify(tithi) == "dark":
        return DARK_TAIL_MALEFIC_WEIGHT
    return 0.0


def is_full_moon(sun_degree, moon_degree):
    """The top-ranked redeemer: the last 3 days before purnima, plus any Moon
    bright enough to be full regardless of which tithi it indexes into."""
    t = tithi_number(sun_degree, moon_degree)
    if t in FULL_MOON_TITHIS:
        return True
    return (classify(t) == "benefic"
            and illumination(sun_degree, moon_degree) >= FULL_MOON_ILLUMINATION)


def has_aspect_power(sun_degree, moon_degree):
    """Can this Moon cast a drishti at all?

    "this cresent moon has no aspect power as it has no light" - so the Moon's
    aspect is gated on luminosity, not on the tithi band. A Moon outside the
    benefic band, or simply too dark, aspects nothing.
    """
    if classify(tithi_number(sun_degree, moon_degree)) != "benefic":
        return False
    return illumination(sun_degree, moon_degree) >= ASPECT_LIGHT_FLOOR


def aspect_power(sun_degree, moon_degree):
    """The Moon's drishti strength, 0.0 - 1.0, scaled by how lit it is.
    0.0 means it casts no aspect at all."""
    if not has_aspect_power(sun_degree, moon_degree):
        return 0.0
    return round(illumination(sun_degree, moon_degree), 3)


def describe(sun_degree, moon_degree):
    """The full Moon-phase fact sheet for one chart.

    This is what the evidence packet carries, so the LLM judge sees the paksha,
    the tithi, whether the Moon can aspect, and how strong its contact is -
    rather than a bare number it has to interpret.
    """
    t = tithi_number(sun_degree, moon_degree)
    paksha = "shukla" if t <= TITHIS_PER_PAKSHA else "krishna"
    in_paksha = t if t <= TITHIS_PER_PAKSHA else t - TITHIS_PER_PAKSHA
    name = TITHI_NAMES[in_paksha - 1] if in_paksha <= len(TITHI_NAMES) else "amavasya"
    if t == 30:
        name = "amavasya"
    band = classify(t)
    return {
        "tithi": t,
        "paksha": paksha,
        "tithi_name": f"{paksha} {name}",
        "separation": round(separation(sun_degree, moon_degree), 2),
        "illumination": round(illumination(sun_degree, moon_degree), 3),
        "band": band,
        "is_full_moon": is_full_moon(sun_degree, moon_degree),
        "benefic_weight": benefic_weight(t),
        "malefic_weight": malefic_weight(t),
        "aspect_power": aspect_power(sun_degree, moon_degree),
        "can_aspect": has_aspect_power(sun_degree, moon_degree),
        "note": {
            "benefic": "waxing/waning Moon inside the panchami-to-dashami band - "
                       "supports whatever it touches",
            "average": "shukla chaturthi - neither helps nor harms",
            "malefic": "dark Moon just past amavasya - afflicts a conjunct planet",
            "dark": "dark run into amavasya - gives nothing, and casts no aspect",
        }[band],
    }
